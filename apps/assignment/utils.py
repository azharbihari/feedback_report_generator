import zlib
import logging
from io import BytesIO
from datetime import datetime
from typing import Dict, List, Any, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)


def process_student_events(student_data: Dict[str, Any]) -> Tuple[Dict[int, str], str, List[Dict[str, Any]]]:
    """
    Process student events data to generate question aliases and event order.

    Args:
        student_data: Dictionary containing student data and events

    Returns:
        Tuple containing:
        - Dictionary mapping unit IDs to question aliases (e.g. {17: 'Q1', 23: 'Q2'})
        - String representing the event order (e.g. 'Q1 -> Q2 -> Q1')
        - List of events with added question aliases
    """
    try:
        events = student_data.get('events', [])
        unit_ids = sorted(set(event['unit'] for event in events))
        aliases = {unit_id: f"Q{i + 1}" for i, unit_id in enumerate(unit_ids)}

        event_order = []
        processed_events = []

        for event in events:
            alias = aliases[event['unit']]
            event_with_alias = {**event, 'question_alias': alias}
            processed_events.append(event_with_alias)
            event_order.append(alias)

        order_string = " -> ".join(event_order)
        return aliases, order_string, processed_events

    except Exception as e:
        logger.error(f"Error processing student events: {str(e)}")
        raise ValueError(f"Failed to process student events: {str(e)}")


def generate_html_report(student_data: Dict[str, Any], event_order: str) -> str:
    """
    Generates an HTML report for the given student data and event order.

    Args:
        student_data: Dictionary containing student data
        event_order: String representing the order of events

    Returns:
        HTML string containing the formatted report
    """
    try:
        student_id = student_data['student_id']
        namespace = student_data['namespace']
        events = student_data.get('events', [])

        _, _, processed_events = process_student_events(student_data)

        def format_time(ts):
            try:
                if isinstance(ts, str):
                    return datetime.fromisoformat(ts.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
                return ts.strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                return ts

        event_rows = "\n".join(
            f"""
            <tr>
                <td>{i+1}</td>
                <td>{event['question_alias']}</td>
                <td>{event['unit']}</td>
                <td>{event['type']}</td>
                <td>{format_time(event['created_time'])}</td>
            </tr>
            """ for i, event in enumerate(processed_events)
        )

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Student Report - {student_id}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                h1 {{
                    color: #2c3e50;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 10px;
                }}
                .info-box {{
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 5px;
                    padding: 15px;
                    margin-bottom: 20px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                table, th, td {{
                    border: 1px solid #dee2e6;
                }}
                th {{
                    background-color: #f2f2f2;
                    padding: 12px;
                }}
                td {{
                    padding: 10px;
                }}
                tr:nth-child(even) {{
                    background-color: #f8f9fa;
                }}
                .footer {{
                    margin-top: 40px;
                    font-size: 0.8em;
                    text-align: center;
                    color: #7f8c8d;
                }}
            </style>
        </head>
        <body>
            <h1>Student Activity Report</h1>

            <div class="info-box">
                <h2>Student Information</h2>
                <p><strong>Student ID:</strong> {student_id}</p>
                <p><strong>Namespace:</strong> {namespace}</p>
                <p><strong>Number of Events:</strong> {len(events)}</p>
            </div>

            <div class="info-box">
                <h2>Event Summary</h2>
                <p><strong>Event Order:</strong> {event_order}</p>
            </div>

            <h2>Detailed Event Timeline</h2>
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Question</th>
                        <th>Unit ID</th>
                        <th>Event Type</th>
                        <th>Timestamp</th>
                    </tr>
                </thead>
                <tbody>
                    {event_rows}
                </tbody>
            </table>

            <div class="footer">
                <p>Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """

    except Exception as e:
        logger.error(f"Error generating HTML report: {str(e)}")
        return f"""
        <html><head><title>Error Report</title></head>
        <body>
        <h1>Error Generating Report</h1>
        <p>{str(e)}</p>
        </body></html>
        """


def generate_pdf_report(student_data: Dict[str, Any], event_order: str) -> bytes:
    """
    Generates a PDF report for the given student data and event order.

    Args:
        student_data: Dictionary containing student data
        event_order: String representing the order of events

    Returns:
        Bytes representing the PDF document
    """
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()

        student_id = student_data['student_id']
        namespace = student_data['namespace']
        _, _, processed_events = process_student_events(student_data)

        elements = [
            Paragraph("Student Activity Report", styles['Heading1']),
            Spacer(1, 0.25 * inch),
            Paragraph("Student Information", styles['Heading2']),
            Paragraph(f"<b>Student ID:</b> {student_id}", styles['Normal']),
            Paragraph(f"<b>Namespace:</b> {namespace}", styles['Normal']),
            Paragraph(f"<b>Number of Events:</b> {len(processed_events)}", styles['Normal']),
            Spacer(1, 0.2 * inch),
            Paragraph("Event Summary", styles['Heading2']),
            Paragraph(f"<b>Event Order:</b> {event_order}", styles['Normal']),
            Spacer(1, 0.2 * inch),
            Paragraph("Detailed Event Timeline", styles['Heading2']),
        ]

        table_data = [['#', 'Question', 'Unit ID', 'Event Type', 'Timestamp']]
        for i, event in enumerate(processed_events):
            try:
                ts = event['created_time']
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    ts = ts.strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                ts = str(event['created_time'])

            table_data.append([
                str(i + 1),
                event['question_alias'],
                str(event['unit']),
                event['type'],
                ts
            ])

        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.5 * inch))
        elements.append(Paragraph(
            f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ParagraphStyle('Footer', parent=styles['Normal'], alignment=1, fontSize=8)
        ))

        doc.build(elements)
        buffer.seek(0)
        return buffer.read()

    except Exception as e:
        logger.error(f"Error generating PDF report: {str(e)}")
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.setTitle("Error Generating Report")
        c.drawString(100, 700, "Error Generating Report")
        c.setFont("Helvetica", 12)
        c.drawString(100, 680, f"An error occurred: {str(e)}")
        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer.read()


def compress_report_content(report_content: bytes) -> bytes:
    """
    Compresses the report content using zlib to save storage space.

    Args:
        report_content: Raw bytes of the report content

    Returns:
        Compressed bytes
    """
    try:
        return zlib.compress(report_content, level=9)
    except Exception as e:
        logger.error(f"Compression failed: {str(e)}")
        raise ValueError(f"Failed to compress report content: {str(e)}")


def decompress_report_content(compressed_content: bytes) -> bytes:
    """
    Decompresses the report content that was previously compressed with zlib.

    Args:
        compressed_content: Compressed bytes from the database

    Returns:
        Decompressed bytes of the original report content
    """
    try:
        return zlib.decompress(compressed_content)
    except zlib.error as e:
        logger.error(f"Decompression failed: {str(e)}")
        raise ValueError(f"Failed to decompress report content: {str(e)}")
