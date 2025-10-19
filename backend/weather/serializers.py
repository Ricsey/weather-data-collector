from rest_framework import serializers


class RollingAverageRequestSerializer(serializers.Serializer):
    city = serializers.CharField(required=True)
    window = serializers.IntegerField(default=7, min_value=1)
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)


class WeatherSyncRequestSerializer(serializers.Serializer):
    city = serializers.CharField(
        required=True,
        max_length=100,
        help_text="City name to sync weather data for",
    )
    force = serializers.BooleanField(
        default=False,
        required=False,
        help_text="Force re-sync even if data already exists",
    )
