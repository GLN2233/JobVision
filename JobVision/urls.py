from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('jobs/', include('jobs.urls')),
    path('', include('home.urls')),
    path('community/', include('community.urls', namespace='community'))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)