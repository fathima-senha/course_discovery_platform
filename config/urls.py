
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.accounts.urls')),
    path('courses/', include('apps.courses.urls')),
    path('interactions/', include('apps.interactions.urls')),
    path('payments/', include('apps.payments.urls')),
    path('admin-panel/', include('apps.adminpanel.urls')),
] 
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)