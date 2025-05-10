from django.urls import path
from .views import GenerateReportView, ReportStatusView, ReportView

app_name = 'assignment'


urlpatterns = [
    path('<str:report_type>', GenerateReportView.as_view(), name='generate_report'),
    path('<str:report_type>/<str:task_id>', ReportStatusView.as_view(), name='report_status'),
    path('reports/<str:task_id>/<uuid:report_id>', ReportView.as_view(), name='report_view'),
]