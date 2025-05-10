import zlib
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from unittest.mock import patch, MagicMock
from .models import ReportTask, GeneratedReport, Status, ReportType


def compress(data: bytes) -> bytes:
    return zlib.compress(data)


class AssignmentAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.html_url = reverse('assignment:generate_report', args=['html'])
        self.pdf_url = reverse('assignment:generate_report', args=['pdf'])
        self.sample_payload = [
            {
                "namespace": "ns_example",
                "student_id": "stu123",
                "events": [
                    {"type": "saved_code", "created_time": "2024-07-21T03:04:55.939000+00:00", "unit": 17},
                    {"type": "submission", "created_time": "2024-07-21T03:10:12.001000+00:00", "unit": 23},
                ]
            }
        ]

    @patch('apps.assignment.views.generate_report_task')
    def test_generate_html_report_returns_202_and_task_id(self, mock_task):
        fake_result = MagicMock()
        fake_result.id = 'task-html-1'
        mock_task.apply_async.return_value = fake_result

        response = self.client.post(self.html_url, data=self.sample_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('task_id', response.data)
        self.assertEqual(response.data['task_id'], fake_result.id)

    @patch('apps.assignment.views.generate_report_task')
    def test_generate_pdf_report_returns_202_and_task_id(self, mock_task):
        fake_result = MagicMock()
        fake_result.id = 'task-pdf-1'
        mock_task.apply_async.return_value = fake_result

        response = self.client.post(self.pdf_url, data=self.sample_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('task_id', response.data)
        self.assertEqual(response.data['task_id'], fake_result.id)

    def test_report_status_pending(self):
        task = ReportTask.objects.create(task_id='t1', status=Status.PENDING, report_type=ReportType.HTML)
        url = reverse('assignment:report_status', args=[ReportType.HTML, task.task_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data['status'], Status.PENDING)

    def test_report_status_success_no_reports(self):
        task = ReportTask.objects.create(task_id='t2', status=Status.SUCCESS, report_type=ReportType.HTML)
        url = reverse('assignment:report_status', args=[ReportType.HTML, task.task_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_report_status_success_with_reports(self):
        task = ReportTask.objects.create(task_id='t3', status=Status.SUCCESS, report_type=ReportType.HTML)
        # create one GeneratedReport
        raw_html = b"<h1>Test</h1>"
        comp = compress(raw_html)
        rpt = GeneratedReport.objects.create(
            report_task=task,
            student_id='stu123',
            namespace='ns',
            content=comp,
            content_type=ReportType.HTML,
        )
        url = reverse('assignment:report_status', args=[ReportType.HTML, task.task_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['report_count'], 1)
        # Compare UUID objects directly
        self.assertEqual(response.data['reports'][0]['id'], rpt.id)

    def test_retrieve_html_report(self):
        # setup report and view
        task = ReportTask.objects.create(task_id='t4', status=Status.SUCCESS, report_type=ReportType.HTML)
        raw_html = b"<h2>Hello</h2>"
        comp = compress(raw_html)
        rpt = GeneratedReport.objects.create(
            report_task=task,
            student_id='stu123',
            namespace='ns',
            content=comp,
            content_type=ReportType.HTML,
        )
        url = reverse('assignment:report_view', args=[task.task_id, rpt.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/html')
        self.assertIn(b"<h2>Hello</h2>", response.content)

    def test_retrieve_pdf_report(self):
        task = ReportTask.objects.create(task_id='t5', status=Status.SUCCESS, report_type=ReportType.PDF)
        raw_pdf = b"PDFDATA"
        comp = compress(raw_pdf)
        rpt = GeneratedReport.objects.create(
            report_task=task,
            student_id='stu123',
            namespace='ns',
            content=comp,
            content_type=ReportType.PDF,
        )
        url = reverse('assignment:report_view', args=[task.task_id, rpt.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertEqual(response.content, raw_pdf)
