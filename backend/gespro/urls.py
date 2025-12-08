"""
URL configuration for gespro project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.views.generic import RedirectView
from proyectos import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('proyectos/',include('proyectos.urls')),
    path('excel/',include('excel.urls')),
    path('alertas/',include('alertas.urls')),
    path('', RedirectView.as_view(url=reverse_lazy('proyectos'))),
    path('vistas/', include('vistas.urls')),
    path('',views.home, name = 'home'),
    path('accounts/', include('allauth.urls')),
    
]

if settings.DEBUG:
    # Include django_browser_reload URLs only in DEBUG mode
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]
