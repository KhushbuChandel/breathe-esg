from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from ingestion.views import UploadView
from review.views import RecordListView, RecordActionView, StatsView

def root(request):
    return JsonResponse({
        'service': 'Breathe ESG API',
        'status': 'running',
    })

def create_admin(request):
    from django.contrib.auth.models import User
    try:
        if User.objects.filter(username='admin').exists():
            u = User.objects.get(username='admin')
            u.set_password('Admin@123')
            u.is_staff = True
            u.is_superuser = True
            u.save()
            return JsonResponse({'message': 'Admin password reset to Admin@123'})
        else:
            User.objects.create_superuser('admin', 'admin@example.com', 'Admin@123')
            return JsonResponse({'message': 'Admin created successfully'})
    except Exception as e:
        return JsonResponse({'error': str(e)})

urlpatterns = [
    path('', root),
    path('setup-admin/', create_admin),  # ← temporary setup URL
    path('admin/', admin.site.urls),
    path('api/upload/', UploadView.as_view()),
    path('api/records/', RecordListView.as_view()),
    path('api/records/<int:pk>/action/', RecordActionView.as_view()),
    path('api/stats/', StatsView.as_view()),
]
