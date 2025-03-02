from django.urls import path
from .views import GenerateReportView, DownloadReportView

urlpatterns = [
    path('download/<int:report_id>/', DownloadReportView.as_view(), name='analytics_download'),
    path('generate/', GenerateReportView.as_view(), name='analytics_generate'),
]
