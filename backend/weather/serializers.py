from rest_framework import serializers


class RollingAverageRequestSerializer(serializers.Serializer):
    city = serializers.CharField(required=True)
    window = serializers.IntegerField(default=7, min_value=1)
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)

    def validate(self, data):
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError(
                {"date_range": "start_date must be before or equal to end_date"}
            )

        return data


class RawDataListQuerySerializer(serializers.Serializer):
    city = serializers.CharField(required=False, max_length=100)
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)

    def validate(self, data):
        """Validate date range."""
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError(
                {"date_range": "start_date must be before or equal to end_date"}
            )

        return data


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
