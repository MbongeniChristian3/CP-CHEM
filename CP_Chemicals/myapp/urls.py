from django.urls import path
from . import views

urlpatterns = [
    # This path handles your traditional Django view at the root URL.
    path('', views.home, name='home'),
    
    # This path handles your DRF view at the 'mymodels/' endpoint.
    path('mymodels/', views.MyModelListCreateView.as_view()),
]
