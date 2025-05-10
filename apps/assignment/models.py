from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid

class Status(models.TextChoices):
    PENDING = 'PENDING', _('Pending')
    STARTED = 'STARTED', _('Started')
    SUCCESS = 'SUCCESS', _('Success')
    FAILURE = 'FAILURE', _('Failure')
    RETRY = 'RETRY', _('Retry')
    REVOKED = 'REVOKED', _('Revoked')

class ReportType(models.TextChoices):
    HTML = 'html', _('HTML')
    PDF = 'pdf', _('PDF')

class ReportTask(models.Model):
    task_id = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_("Task ID"),
        help_text=_("Unique identifier for the task."),
        db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name=_("Task Status"),
        help_text=_("The current status of the report generation task."),
        db_index=True
    )
    report_type = models.CharField(
        max_length=10,
        choices=ReportType.choices,
        default=ReportType.HTML,
        verbose_name=_("Report Type"),
        help_text=_("The type of the report being generated (either HTML or PDF)."),
        db_index=True
    )
    error_message = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Error Message"),
        help_text=_("Optional error message if task fails.")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Creation Time"),
        help_text=_("Timestamp when the task was created."),
        db_index=True
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Last Updated Time"),
        help_text=_("Timestamp when the task status was last updated.")
    )

    def __str__(self):
        return f"Task {self.task_id} - {self.get_status_display()}"

    class Meta:
        verbose_name = _("Report Generation Task")
        verbose_name_plural = _("Report Generation Tasks")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'report_type']),
        ]

class GeneratedReport(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("Report ID"),
        help_text=_("Unique identifier for the report.")
    )
    report_task = models.ForeignKey(
        ReportTask,
        on_delete=models.CASCADE,
        related_name='generated_reports',
        verbose_name=_("Related Task"),
        help_text=_("The report task this report is associated with.")
    )
    student_id = models.CharField(
        max_length=255,
        verbose_name=_("Student ID"),
        help_text=_("The unique ID of the student."),
        db_index=True
    )
    namespace = models.CharField(
        max_length=255,
        verbose_name=_("Namespace"),
        help_text=_("The namespace associated with the report."),
        db_index=True
    )
    content = models.BinaryField(
        null=True,
        blank=True,
        verbose_name=_("Report Content"),
        help_text=_("Binary content of the report (e.g., PDF or HTML as bytes), compressed using zlib.")
    )
    content_type = models.CharField(
        max_length=10,
        choices=ReportType.choices,
        verbose_name=_("Report Type"),
        help_text=_("The type of content in the report, either HTML or PDF."),
        db_index=True
    )
    generated_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Generated Time"),
        help_text=_("Timestamp when the report was generated."),
        db_index=True
    )
    file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Compressed Size (bytes)"),
        help_text=_("Size of the compressed report content in bytes.")
    )

    def __str__(self):
        return f"Generated {self.content_type} Report for {self.student_id}"

    def save(self, *args, **kwargs):
        if self.content:
            self.file_size = len(self.content)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Generated Report")
        verbose_name_plural = _("Generated Reports")
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['student_id']),
            models.Index(fields=['namespace']),
            models.Index(fields=['report_task', 'content_type']),
            models.Index(fields=['student_id', 'namespace']),
        ]
