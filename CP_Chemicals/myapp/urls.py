from django.urls import path
from . import views

urlpatterns = [
    # The 'path' function maps a URL to a view function.
    # The empty string '' represents the root URL (e.g., http://127.0.0.1:8000/).
    # It calls the 'home' function from the 'views.py' file.
    path('', views.home, name='home'),
]