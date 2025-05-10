from django.contrib import admin
from .models import ReportTask, GeneratedReport

@admin.register(ReportTask)
class ReportTaskAdmin(admin.ModelAdmin):
    list_display = ('task_id', 'status', 'report_type', 'created_at', 'updated_at')
    list_filter = ('status', 'report_type', 'created_at')
    search_fields = ('task_id',)

@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'namespace', 'report_task', 'content_type', 'generated_at')
    list_filter = ('content_type', 'generated_at')
    search_fields = ('student_id', 'namespace', 'report_task__task_id')
