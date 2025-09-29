# myapp/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router for the Sales ViewSets
router = DefaultRouter()
router.register(r'sales-orders', views.SalesOrderViewSet, basename='sales-order')
router.register(r'sales-order-items', views.SalesOrderItemViewSet, basename='sales-order-item')
router.register(r'products', views.ProductViewSet, basename='product') # It's good practice to register this one too

urlpatterns = [
    # Traditional web page
    path('', views.home, name='home'),
    
    # Authentication API endpoints
    path('api/login/', views.login_view, name='login'),
    path('api/register/', views.register_view, name='register'),
    path('api/user/', views.user_profile_view, name='user_profile'),
    path('api/logout/', views.logout_view, name='logout'),
    
    # Your existing API endpoints (make sure these are correct for your current views)
    # The following URLs were commented out in views.py, so they should be removed from here too.
    # path('api/mymodel/', views.MyModelListCreateView.as_view(), name='mymodel-list-create'),
    # path('api/products/', views.ProductListCreateView.as_view(), name='product-list-create'),
    # path('api/products/<uuid:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    
    # Integrate the sales views via the router, replacing the old quotation views
    path('api/', include(router.urls)),
]