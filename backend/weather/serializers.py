from rest_framework import serializers


class RollingAverageRequestSerializer(serializers.Serializer):
    city = serializers.CharField(required=True)
    window = serializers.IntegerField(default=7, min_value=1)
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
