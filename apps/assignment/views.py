from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
import logging

from .models import ReportTask, Status, ReportType, GeneratedReport
from .serializers import StudentDataSerializer
from .tasks import generate_report_task
from .utils import decompress_report_content

logger = logging.getLogger(__name__)

class GenerateReportView(APIView):
    """
    Initiates asynchronous report generation for student event data.
    """
    def post(self, request, report_type):
        valid_types = [choice.value for choice in ReportType]
        if report_type not in valid_types:
            return Response(
                {'error': f"Invalid report_type. Must be one of: {', '.join(valid_types)}."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            serializer = StudentDataSerializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
        except ValidationError as e:
            return Response({'error': 'Invalid data format', 'details': e.detail}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        try:
            report_task = ReportTask.objects.create(status=Status.PENDING, report_type=report_type)
            async_result = generate_report_task.apply_async(
                kwargs={'task_pk': report_task.pk, 'data': validated_data, 'report_type': report_type}
            )
            report_task.task_id = async_result.id
            report_task.save(update_fields=["task_id"])
            
            status_url = request.build_absolute_uri(
                reverse('assignment:report_status', args=[report_type, async_result.id])
            )
            
            return Response(
                {
                    'task_id': async_result.id,
                    'status': Status.PENDING,
                    'status_url': status_url
                },
                status=status.HTTP_202_ACCEPTED,
                headers={'Location': status_url}
            )
        except Exception as e:
            logger.error(f"Error creating report task: {str(e)}")
            return Response(
                {'error': 'Failed to create report task', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReportStatusView(APIView):
    """
    Checks the status of a report generation task and returns the result if completed.
    """
    def get(self, request, report_type, task_id):
        valid_types = [choice.value for choice in ReportType]
        if report_type not in valid_types:
            return Response(
                {'error': f"Invalid report_type. Must be one of: {', '.join(valid_types)}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            task = get_object_or_404(ReportTask, task_id=task_id, report_type=report_type)

            if task.status in {Status.PENDING, Status.STARTED, Status.RETRY}:
                return Response(
                    {
                        'status': task.status,
                        'message': f"Report generation is {task.status.lower()}. Please check back later."
                    }, 
                    status=status.HTTP_202_ACCEPTED
                )

            if task.status == Status.FAILURE:
                return Response(
                    {
                        'status': task.status, 
                        'error': task.error_message
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            if task.status == Status.REVOKED:
                return Response(
                    {
                        'status': task.status, 
                        'message': 'Task was revoked'
                    },
                    status=status.HTTP_410_GONE
                )

            reports_qs = GeneratedReport.objects.filter(report_task=task, content_type=report_type)
            if not reports_qs.exists():
                return Response(
                    {
                        'status': task.status,
                        'error': 'No reports found even though task completed successfully.'
                    }, 
                    status=status.HTTP_404_NOT_FOUND
                )

            reports = [
                {
                    'id': rpt.id,
                    'student_id': rpt.student_id,
                    'namespace': rpt.namespace,
                    'generated_at': rpt.generated_at.isoformat(),
                    'url': request.build_absolute_uri(
                        reverse('assignment:report_view', args=[task.task_id, rpt.id])
                    )
                }
                for rpt in reports_qs
            ]

            return Response(
                {
                    'status': task.status, 
                    'task_id': task.task_id,
                    'report_type': task.report_type,
                    'created_at': task.created_at.isoformat(),
                    'updated_at': task.updated_at.isoformat(),
                    'report_count': len(reports),
                    'reports': reports
                }, 
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving task status: {str(e)}")
            return Response(
                {'error': 'Error retrieving task status', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReportView(APIView):
    """
    Returns the content of a generated report as HTML or PDF.
    """
    def get(self, request, task_id, report_id):
        try:
            report = get_object_or_404(GeneratedReport, report_task__task_id=task_id, id=report_id)
            filename = f"Report-{report.student_id}.{report.content_type}"

            try:
                raw_data = decompress_report_content(report.content)
            except Exception as e:
                logger.error(f"Decompression failed for report {report_id}: {str(e)}")
                return Response(
                    {'error': f"Failed to decompress report content: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            if report.content_type == ReportType.HTML:
                try:
                    data = raw_data.decode('utf-8')
                    resp = HttpResponse(data, content_type='text/html')
                    resp['Content-Disposition'] = f'inline; filename="{filename}"'
                except UnicodeDecodeError as e:
                    logger.error(f"Unicode decode error for HTML report {report_id}: {str(e)}")
                    return Response(
                        {'error': f"Failed to decode HTML content: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            elif report.content_type == ReportType.PDF:
                resp = HttpResponse(raw_data, content_type='application/pdf')
                resp['Content-Disposition'] = f'inline; filename="{filename}"'

            else:
                return Response(
                    {'error': f"Unsupported report type: {report.content_type}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return resp
        except Exception as e:
            logger.error(f"Error retrieving report: {str(e)}")
            return Response(
                {'error': 'Error retrieving report', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
