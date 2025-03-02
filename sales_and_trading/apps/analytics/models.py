from django.db import models

class AnalyticsReport(models.Model):
    report_name = models.CharField(max_length=200)
    file = models.FileField(upload_to='reports/', null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.report_name} ({self.generated_at})"
