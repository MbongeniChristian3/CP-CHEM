# myapp/views.py
from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
import json

from .models import MyModel
from .serializers import MyModelSerializer
from .permissions import HasWarehouseAccess

# Django View for a traditional web page
def home(request):
    return render(request, 'myapp/home.html')

# Authentication Views
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Handle user login and return JWT tokens
    """
    try:
        data = request.data
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return Response({
                'success': False,
                'message': 'Username and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Authenticate user
        user = authenticate(username=username, password=password)
        
        if user is not None:
            if user.is_active:
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                access_token = refresh.access_token
                
                # Get user profile info (if you have a profile model)
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                }
                
                # Add profile data if profile exists
                try:
                    if hasattr(user, 'profile'):
                        user_data.update({
                            'role': user.profile.role,
                            'warehouse': user.profile.warehouse.name if user.profile.warehouse else None,
                        })
                except:
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
                return Response({
                    'success': False,
                    'message': 'Account is inactive'
                }, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({
                'success': False,
                'message': 'Invalid username or password'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Login error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """
    Handle user registration
    """
    try:
        data = request.data
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        
        # Validation
        if not username or not email or not password:
            return Response({
                'success': False,
                'message': 'Username, email, and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            return Response({
                'success': False,
                'message': 'Username already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if User.objects.filter(email=email).exists():
            return Response({
                'success': False,
                'message': 'Email already registered'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create user
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
        return Response({
            'success': False,
            'message': f'Registration error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def user_profile_view(request):
    """
    Get current user profile
    """
    if request.user.is_authenticated:
        user_data = {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
        }
        
        # Add profile data if exists
        try:
            if hasattr(request.user, 'profile'):
                user_data.update({
                    'role': request.user.profile.role,
                    'warehouse': request.user.profile.warehouse.name if request.user.profile.warehouse else None,
                })
        except:
            pass
            
        return Response({
            'success': True,
            'user': user_data
        })
    else:
        return Response({
            'success': False,
            'message': 'Not authenticated'
        }, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def logout_view(request):
    """
    Handle user logout (if using JWT, mainly for client-side token removal)
    """
    return Response({
        'success': True,
        'message': 'Logged out successfully'
    })

# Your existing Django REST Framework View
class MyModelListCreateView(generics.ListCreateAPIView):
    serializer_class = MyModelSerializer
    permission_classes = [HasWarehouseAccess]
    
    def get_queryset(self):
        """
        This view should return a list of all MyModels for
        CEOs and Chairmen, and a filtered list for others.
        """
        user = self.request.user
        
        # CEOs and Chairmen can see all MyModel objects
        if user.profile.role in ['ceo', 'chairman']:
            return MyModel.objects.all()
        
        # All other roles (Manager, Cashier, Dispatch) can only see objects
        # associated with their assigned warehouse.
        return MyModel.objects.filter(warehouse=user.profile.warehouse)