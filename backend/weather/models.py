from django.db import models


class WeatherData(models.Model):
    time = models.DateField(unique=True)
    t_max = models.FloatField()
    t_mean = models.FloatField()
    t_min = models.FloatField()
    city = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["time"]

    def __str__(self) -> str:
        return f"{self.time}: max={self.t_max}, mean={self.t_mean}, min={self.t_min}"
