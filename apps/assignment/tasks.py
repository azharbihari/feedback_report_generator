import logging
from celery import shared_task
from pydantic import ValidationError
from celery.exceptions import MaxRetriesExceededError
from django.db import transaction

from .schemas import StudentSchema
from .utils import (
    generate_html_report, 
    generate_pdf_report, 
    compress_report_content,
    process_student_events
)
from .models import ReportTask, Status, GeneratedReport, ReportType

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_report_task(self, task_pk: int, data: list, report_type: str):
    """
    Asynchronous Celery task to generate reports for student data.

    Args:
        task_pk (int): Primary key of the ReportTask model.
        data (list): List of student data dictionaries.
        report_type (str): Desired format of report (e.g., 'html', 'pdf').

    Returns:
        dict: Summary of the task outcome.
    """
    logger.info(f"Task {self.request.id} started for ReportTask ID: {task_pk}")

    if report_type not in [choice.value for choice in ReportType]:
        error_msg = f"Invalid report_type: {report_type}"
        logger.error(error_msg)
        _update_task_status(task_pk, Status.FAILURE, error_msg)
        return {"status": "error", "message": error_msg}

    try:
        task = ReportTask.objects.get(pk=task_pk)
        task.status = Status.STARTED
        task.save(update_fields=["status"])
    except ReportTask.DoesNotExist:
        error_msg = f"ReportTask with ID {task_pk} not found."
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}

    try:
        students = [StudentSchema.model_validate(item) for item in data]
        logger.info(f"Validated {len(students)} student entries.")

        successful, failed = 0, 0

        with transaction.atomic():
            for student in students:
                try:
                    student_dict = student.model_dump()
                    student_id = student.student_id
                    namespace = student.namespace

                    aliases, event_order, _ = process_student_events(student_dict)

                    if report_type == ReportType.HTML:
                        raw_report = generate_html_report(student_dict, event_order).encode('utf-8')
                    else:
                        raw_report = generate_pdf_report(student_dict, event_order)

                    compressed = compress_report_content(raw_report)

                    GeneratedReport.objects.create(
                        report_task=task,
                        student_id=student_id,
                        namespace=namespace,
                        content=compressed,
                        content_type=report_type
                    )

                    successful += 1
                    logger.info(f"Report generated for student {student_id}.")

                except Exception as e:
                    failed += 1
                    logger.exception(f"Failed report for student {student.student_id}: {e}")

        if successful and not failed:
            task.status = Status.SUCCESS
            logger.info(f"Task {task_pk} completed: all {successful} reports successful.")
        elif successful:
            task.status = Status.SUCCESS
            task.error_message = f"{successful} reports succeeded, {failed} failed."
            logger.warning(f"Task {task_pk} partially successful.")
        else:
            task.status = Status.FAILURE
            task.error_message = "All report generations failed."
            logger.error(f"Task {task_pk} failed completely.")

        task.save(update_fields=["status", "error_message"] if task.error_message else ["status"])

        return {
            "status": task.status,
            "successful_reports": successful,
            "failed_reports": failed
        }

    except ValidationError as ve:
        error_msg = f"Validation error: {ve.json()}"
        logger.error(error_msg)
        _update_task_status(task_pk, Status.FAILURE, error_msg)
        return {"status": "error", "message": error_msg}

    except MaxRetriesExceededError as mre:
        error_msg = f"Max retries exceeded: {mre}"
        logger.error(error_msg)
        _update_task_status(task_pk, Status.FAILURE, error_msg)
        return {"status": "error", "message": "Max retries exceeded"}

    except Exception as e:
        logger.exception(f"Unexpected error in task {task_pk}: {e}")
        try:
            raise self.retry(exc=e)
        except MaxRetriesExceededError:
            error_msg = "Max retries exceeded on unexpected error."
            logger.error(error_msg)
            _update_task_status(task_pk, Status.FAILURE, error_msg)
            return {"status": "error", "message": error_msg}


def _update_task_status(task_pk: int, status: str, error_message: str = None):
    """
    Updates the task's status and logs the outcome.

    Args:
        task_pk (int): Primary key of the ReportTask.
        status (str): New status value.
        error_message (str, optional): Error message if failed.
    """
    try:
        task = ReportTask.objects.get(pk=task_pk)
        task.status = status
        if error_message:
            task.error_message = error_message
        task.save()
        logger.info(f"Task {task_pk} updated to status: {status}")
    except ReportTask.DoesNotExist:
        logger.error(f"Failed to update status. ReportTask ID {task_pk} not found.")
    except Exception as e:
        logger.exception(f"Error while updating task {task_pk} status: {e}")
