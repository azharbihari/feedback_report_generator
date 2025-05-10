from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

class EventSerializer(serializers.Serializer):
    type = serializers.ChoiceField(
        choices=['saved_code', 'submission'],
        help_text=_("The type of event (either saved_code or submission)")
    )
    created_time = serializers.DateTimeField(
        help_text=_("Timestamp when the event occurred")
    )
    unit = serializers.IntegerField(
        min_value=0,
        help_text=_("Unit ID associated with the event")
    )

    def validate_unit(self, value):
        if value < 0:
            raise serializers.ValidationError(_("Unit ID must be a non-negative integer"))
        return value


class StudentDataSerializer(serializers.Serializer):
    namespace = serializers.CharField(
        max_length=255,
        help_text=_("Namespace the student belongs to")
    )
    student_id = serializers.CharField(
        max_length=255,
        help_text=_("Unique identifier for the student")
    )
    events = EventSerializer(
        many=True,
        help_text=_("List of events associated with the student")
    )

    def validate_namespace(self, value):
        if not value.strip():
            raise serializers.ValidationError(_("Namespace cannot be empty"))
        return value

    def validate_student_id(self, value):
        if not value.strip():
            raise serializers.ValidationError(_("Student ID cannot be empty"))
        return value

    def validate_events(self, value):
        if not value:
            raise serializers.ValidationError(_("At least one event is required"))
        return value


class ReportTaskSerializer(serializers.Serializer):
    task_id = serializers.CharField(
        help_text=_("Unique identifier for the task")
    )
    status = serializers.CharField(
        help_text=_("Current status of the task")
    )
    report_type = serializers.CharField(
        help_text=_("Type of report being generated")
    )
    created_at = serializers.DateTimeField(
        help_text=_("Timestamp when the task was created")
    )
    updated_at = serializers.DateTimeField(
        help_text=_("Timestamp when the task was last updated")
    )


class GeneratedReportSerializer(serializers.Serializer):
    id = serializers.UUIDField(
        help_text=_("Unique identifier for the report")
    )
    student_id = serializers.CharField(
        help_text=_("Student ID associated with the report")
    )
    namespace = serializers.CharField(
        help_text=_("Namespace associated with the report")
    )
    content_type = serializers.CharField(
        help_text=_("Type of the report content (HTML or PDF)")
    )
    generated_at = serializers.DateTimeField(
        help_text=_("Timestamp when the report was generated")
    )
    file_size = serializers.IntegerField(
        help_text=_("Size of the compressed report content in bytes")
    )
    url = serializers.URLField(
        help_text=_("URL to retrieve the report content")
    )
