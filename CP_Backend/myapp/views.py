# myapp/views.py
# myapp/views.py

from django.shortcuts import render
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import generics, status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
# --- FIX: Import DjangoModelPermissions to utilize permissions set in Django Admin ---
from rest_framework.permissions import AllowAny, IsAuthenticated, DjangoModelPermissions 
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

# Assuming these imports are correct
from .models import Product, SalesOrder, SalesOrderItem 
from .serializers import (
    ProductSerializer, 
    SalesOrderDetailSerializer, 
    SalesOrderItemSerializer,
    SalesOrderCreateUpdateSerializer 
)
# NOTE: HasWarehouseAccess is not imported or used, as it was causing the 403 error.
# The functionality is moved to standard DRF/Django permissions.


# ================= Django View ==================

def home(request):
    """Traditional Django view for a web page."""
    return render(request, 'myapp/home.html')

# ================= AUTH VIEWS ==================
# These views are fine. No changes were strictly needed to resolve the reported ViewSet errors.

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Handle user login and return JWT tokens."""
    try:
        data = request.data
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return Response({
                'success': False,
                'message': 'Username and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                refresh = RefreshToken.for_user(user)
                access_token = refresh.access_token

                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                }

                # Attempt to retrieve profile data securely
                try:
                    profile = getattr(user, 'profile', None)
                    if profile:
                        user_data.update({
                            'role': profile.role,
                            'warehouse': profile.warehouse.name if profile.warehouse else None,
                        })
                except Exception:
                    # Ignore profile retrieval errors (user still logs in)
                    pass 

                return Response({
                    'success': True,
                    'message': 'Login successful',
                    'user': user_data,
                    'tokens': {
                        'access': str(access_token),
                        'refresh': str(refresh),
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({'success': False, 'message': 'Account is inactive'},
                                 status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({'success': False, 'message': 'Invalid username or password'},
                             status=status.HTTP_401_UNAUTHORIZED)

    except Exception as e:
        return Response({'success': False, 'message': f'Login error: {str(e)}'},
                         status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """Handle user registration"""
    try:
        data = request.data
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')

        if not username or not email or not password:
            return Response({'success': False, 'message': 'Username, email, and password are required'},
                             status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({'success': False, 'message': 'Username already exists'},
                             status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({'success': False, 'message': 'Email already registered'},
                             status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        return Response({
            'success': True,
            'message': 'Account created successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            }
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'success': False, 'message': f'Registration error: {str(e)}'},
                         status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile_view(request):
    """Get current user profile"""
    user_data = {
        'id': request.user.id,
        'username': request.user.username,
        'email': request.user.email,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
    }

    try:
        profile = getattr(request.user, 'profile', None)
        if profile:
            user_data.update({
                'role': profile.role,
                'warehouse': profile.warehouse.name if profile.warehouse else None,
            })
    except Exception:
        pass

    return Response({'success': True, 'user': user_data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Handle user logout (JWT: handled client-side)"""
    return Response({'success': True, 'message': 'Logged out successfully'})


# ================= BASE VIEWS ==================
class BaseModelViewSet(viewsets.ModelViewSet):
    """
    A base class for all ViewSets. It handles authorization via DjangoModelPermissions
    and applies warehouse-based filtering to the queryset.
    """
    # --- FIX 1: Use DjangoModelPermissions to fix the 403 Forbidden error ---
    permission_classes = [DjangoModelPermissions]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    def get_queryset(self):
        """
        Filters the queryset based on the user's role and assigned warehouse.
        """
        user = self.request.user
        
        if not user.is_authenticated:
             return self.queryset.none()
             
        # Allow full access for CEO/Chairman or Superusers
        if user.is_superuser or (hasattr(user, "profile") and user.profile.role in ["ceo", "chairman"]):
            return self.queryset.all()
        
        # Restrict by user's warehouse
        if hasattr(user, "profile") and user.profile.warehouse:
            # Check if the model has a 'warehouse' field to filter by
            if hasattr(self.queryset.model, 'warehouse'):
                return self.queryset.filter(warehouse=user.profile.warehouse)
                
        # Deny access if user is authenticated but doesn't meet role/warehouse criteria
        return self.queryset.none()
    
    
# ================= NEW SALES VIEWS ==================
class SalesOrderViewSet(BaseModelViewSet):
    """
    A ViewSet for managing Sales Orders.
    """
    queryset = SalesOrder.objects.all()
    serializer_class = SalesOrderDetailSerializer 
    # NOTE: Assuming 'warehouse' is a field on SalesOrder. If you get a TypeError here, remove 'warehouse'.
    filterset_fields = ['status', 'warehouse']
    search_fields = ['quotation_number', 'customer_name']
    ordering_fields = ['created_at', 'total_amount']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SalesOrderCreateUpdateSerializer
        return SalesOrderDetailSerializer

    def perform_create(self, serializer):
        # Automatically set the created_by user and warehouse
        serializer.save(created_by=self.request.user, warehouse=self.request.user.profile.warehouse)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Action to confirm a sales order."""
        sales_order = self.get_object()
        sales_order.status = 'approved'
        sales_order.save()
        return Response({'success': True, 'message': f'Sales order {sales_order.quotation_number} confirmed.'})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Action to cancel a sales order."""
        sales_order = self.get_object()
        sales_order.status = 'cancelled'
        sales_order.save()
        return Response({'success': True, 'message': f'Sales order {sales_order.quotation_number} cancelled.'})
        
        
class SalesOrderItemViewSet(BaseModelViewSet):
    """
    A ViewSet for managing Sales Order Items.
    """
    queryset = SalesOrderItem.objects.all()
    serializer_class = SalesOrderItemSerializer
    filterset_fields = ['sales_order'] # 'sales_order' is a related field, which is usually fine for filtering.
    
    def get_queryset(self):
        queryset = super().get_queryset()
        sales_order_id = self.request.query_params.get('sales_order_id')
        if sales_order_id:
            queryset = queryset.filter(sales_order__id=sales_order_id)
        return queryset


# ================= PRODUCT VIEWS ==================
class ProductViewSet(BaseModelViewSet):
    """
    A ViewSet for managing Products.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    # --- FIX 2: Removed 'warehouse' from filterset_fields to resolve TypeError (500) ---
    # The BaseModelViewSet handles filtering by warehouse in get_queryset.
    filterset_fields = ['category'] 
    search_fields = ['name', 'formula', 'sku']