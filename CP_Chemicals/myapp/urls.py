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
    path('api/mymodel/', views.MyModelListCreateView.as_view(), name='mymodel-list-create'),
    
    # Product API endpoints
    path('api/products/', views.ProductListCreateView.as_view(), name='product-list-create'),
    path('api/products/<uuid:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    
    # Quotation API endpoints
    path('api/quotations/', views.QuotationListView.as_view(), name='quotation-list'),
    path('api/quotations/create/', views.QuotationCreateView.as_view(), name='quotation-create'),
    path('api/quotations/<uuid:pk>/', views.QuotationDetailView.as_view(), name='quotation-detail'),
    path('api/quotations/<uuid:pk>/update/', views.QuotationUpdateView.as_view(), name='quotation-update'),
    path('api/quotations/<uuid:pk>/delete/', views.QuotationDeleteView.as_view(), name='quotation-delete'),
    path('api/quotations/<uuid:pk>/status/', views.update_quotation_status, name='quotation-status-update'),
    
    # Quotation Item API endpoints
    path('api/quotations/<uuid:quotation_id>/items/', views.add_quotation_item, name='add-quotation-item'),
    path('api/quotations/<uuid:quotation_id>/items/<uuid:item_id>/', views.quotation_item_detail, name='quotation-item-detail'),
]