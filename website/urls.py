from django.urls import path
from .views import get_available_times

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('get-available-times/', get_available_times, name='get_available_times'),
]
