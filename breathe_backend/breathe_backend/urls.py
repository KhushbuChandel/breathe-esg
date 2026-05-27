from django.contrib import admin
from django.urls import path
from ingestion.views import UploadView
from review.views import RecordListView, RecordActionView, StatsView
from django.http import JsonResponse
def root(request):
    return JsonResponse({
        'service': 'Breathe ESG API',
        'status': 'running',
        'endpoints': ['/api/records/', '/api/stats/', '/api/upload/', '/admin/']
    })

urlpatterns = [
    path('', root),
    path('admin/', admin.site.urls),
    path('api/upload/', UploadView.as_view()),
    path('api/records/', RecordListView.as_view()),
    path('api/records/<int:pk>/action/', RecordActionView.as_view()),
    path('api/stats/', StatsView.as_view()),
]