# myapp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Traditional web page
    path('', views.home, name='home'),
    
    # Authentication API endpoints
    path('api/login/', views.login_view, name='login'),
    path('api/register/', views.register_view, name='register'),
    path('api/user/', views.user_profile_view, name='user_profile'),
    path('api/logout/', views.logout_view, name='logout'),
    
    # Your existing API endpoint
    path('api/mymodel/', views.MyModelListCreateView.as_view(), name='mymodel-list-create')
]