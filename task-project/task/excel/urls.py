from .models import Cards
from django.urls import path
from . import views
from django.contrib import admin
urlspatterns = [
    path('admin/',admin.site.urls)
] 