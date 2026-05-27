from django.contrib import admin
from django.urls import path
from ingestion.views import UploadView
from review.views import RecordListView, RecordActionView, StatsView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/upload/', UploadView.as_view()),
    path('api/records/', RecordListView.as_view()),
    path('api/records/<int:pk>/action/', RecordActionView.as_view()),
    path('api/stats/', StatsView.as_view()),
]