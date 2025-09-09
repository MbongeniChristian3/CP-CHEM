# myapp/views.py
from django.shortcuts import render
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import MyModel, Product
from .serializers import MyModelSerializer, ProductSerializer
from .permissions import HasWarehouseAccess


# Django View for a traditional web page
def home(request):
    return render(request, 'myapp/home.html')


# ================= AUTH VIEWS ==================
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Handle user login and return JWT tokens"""
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

                try:
                    if hasattr(user, 'profile'):
                        user_data.update({
                            'role': user.profile.role,
                            'warehouse': user.profile.warehouse.name if user.profile.warehouse else None,
                        })
                except Exception:
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
def user_profile_view(request):
    """Get current user profile"""
    if request.user.is_authenticated:
        user_data = {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
        }

        try:
            if hasattr(request.user, 'profile'):
                user_data.update({
                    'role': request.user.profile.role,
                    'warehouse': request.user.profile.warehouse.name if request.user.profile.warehouse else None,
                })
        except Exception:
            pass

        return Response({'success': True, 'user': user_data})

    return Response({'success': False, 'message': 'Not authenticated'},
                    status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
def logout_view(request):
    """Handle user logout (JWT: handled client-side)"""
    return Response({'success': True, 'message': 'Logged out successfully'})


# ================= QUOTATION VIEWS ==================
class QuotationListView(generics.ListCreateAPIView):
    """
    API view for listing and creating quotations
    GET: Returns list of quotations based on user permissions
    POST: Creates a new quotation
    """
    permission_classes = [HasWarehouseAccess]
    
    def get_queryset(self):
        """Return quotations based on user role and warehouse access"""
        user = self.request.user
        
        # If you have a Quotation model, uncomment and modify this:
        # if hasattr(user, "profile") and user.profile.role in ["ceo", "chairman"]:
        #     return Quotation.objects.all()
        # if hasattr(user, "profile") and user.profile.warehouse:
        #     return Quotation.objects.filter(warehouse=user.profile.warehouse)
        # return Quotation.objects.none()
        
        # For now, return empty queryset to prevent errors
        from django.db import models
        return models.QuerySet(model=None)
    
    def list(self, request, *args, **kwargs):
        """Custom list method to return sample data until Quotation model is ready"""
        user = request.user
        
        # Sample quotation data - replace with actual model data
        sample_quotations = []
        
        if hasattr(user, 'profile'):
            if user.profile.role in ["ceo", "chairman"]:
                # CEO/Chairman can see all quotations
                sample_quotations = [
                    {
                        "id": 1,
                        "quotation_number": "QUO-001",
                        "customer": "ABC Chemicals Ltd",
                        "warehouse": "Main Warehouse",
                        "total_amount": 5000.00,
                        "status": "pending",
                        "created_at": "2024-01-15"
                    },
                    {
                        "id": 2,
                        "quotation_number": "QUO-002", 
                        "customer": "XYZ Industries",
                        "warehouse": "Secondary Warehouse",
                        "total_amount": 7500.00,
                        "status": "approved",
                        "created_at": "2024-01-16"
                    }
                ]
            elif user.profile.warehouse:
                # Regular users see only their warehouse quotations
                warehouse_name = user.profile.warehouse.name
                sample_quotations = [
                    {
                        "id": 1,
                        "quotation_number": "QUO-001",
                        "customer": "Local Customer",
                        "warehouse": warehouse_name,
                        "total_amount": 3000.00,
                        "status": "pending",
                        "created_at": "2024-01-15"
                    }
                ]
        
        return Response({
            "success": True,
            "count": len(sample_quotations),
            "quotations": sample_quotations
        }, status=status.HTTP_200_OK)
    
    def create(self, request, *args, **kwargs):
        """Create a new quotation"""
        data = request.data
        user = request.user
        
        # Basic validation
        required_fields = ['customer', 'items']
        for field in required_fields:
            if not data.get(field):
                return Response({
                    'success': False,
                    'message': f'{field.title()} field is required'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Here you would create the quotation using your Quotation model
        # quotation_data = {
        #     'customer': data.get('customer'),
        #     'items': data.get('items'),
        #     'warehouse': user.profile.warehouse if hasattr(user, 'profile') else None,
        #     'created_by': user
        # }
        # quotation = Quotation.objects.create(**quotation_data)
        
        # For now, return sample response
        response_data = {
            "success": True,
            "message": "Quotation created successfully",
            "quotation": {
                "id": 3,  # This would be the actual ID from your model
                "quotation_number": "QUO-003",
                "customer": data.get('customer'),
                "warehouse": user.profile.warehouse.name if hasattr(user, 'profile') and user.profile.warehouse else 'Unknown',
                "status": "draft",
                "items": data.get('items', [])
            }
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)


class QuotationCreateView(generics.CreateAPIView):
    """
    API view specifically for creating quotations
    """
    permission_classes = [HasWarehouseAccess]
    
    def create(self, request, *args, **kwargs):
        """Create a new quotation"""
        data = request.data
        user = request.user
        
        # Basic validation
        required_fields = ['customer', 'items']
        for field in required_fields:
            if not data.get(field):
                return Response({
                    'success': False,
                    'message': f'{field.title()} field is required'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Here you would create the quotation using your Quotation model
        # quotation_data = {
        #     'customer': data.get('customer'),
        #     'items': data.get('items'),
        #     'warehouse': user.profile.warehouse if hasattr(user, 'profile') else None,
        #     'created_by': user
        # }
        # quotation = Quotation.objects.create(**quotation_data)
        
        # For now, return sample response
        response_data = {
            "success": True,
            "message": "Quotation created successfully",
            "quotation": {
                "id": 3,  # This would be the actual ID from your model
                "quotation_number": "QUO-003",
                "customer": data.get('customer'),
                "warehouse": user.profile.warehouse.name if hasattr(user, 'profile') and user.profile.warehouse else 'Unknown',
                "status": "draft",
                "items": data.get('items', [])
            }
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)


class QuotationUpdateView(generics.UpdateAPIView):
    """
    API view specifically for updating quotations
    """
    permission_classes = [HasWarehouseAccess]
    
    def get_queryset(self):
        """Return quotations based on user role and warehouse access"""
        user = self.request.user
        
        # If you have a Quotation model, uncomment and modify this:
        # if hasattr(user, "profile") and user.profile.role in ["ceo", "chairman"]:
        #     return Quotation.objects.all()
        # if hasattr(user, "profile") and user.profile.warehouse:
        #     return Quotation.objects.filter(warehouse=user.profile.warehouse)
        # return Quotation.objects.none()
        
        # For now, return empty queryset to prevent errors
        from django.db import models
        return models.QuerySet(model=None)
    
    def update(self, request, pk, *args, **kwargs):
        """Update a specific quotation"""
        data = request.data
        user = request.user
        
        # Here you would fetch and update the quotation
        # try:
        #     quotation = self.get_queryset().get(pk=pk)
        #     # Update fields
        #     for field, value in data.items():
        #         if hasattr(quotation, field):
        #             setattr(quotation, field, value)
        #     quotation.save()
        # except Quotation.DoesNotExist:
        #     return Response({'success': False, 'message': 'Quotation not found'}, 
        #                   status=status.HTTP_404_NOT_FOUND)
        
        # For now, return sample response
        response_data = {
            "success": True,
            "message": "Quotation updated successfully",
            "quotation": {
                "id": str(pk),  # UUID as string
                "quotation_number": f"QUO-{str(pk)[:8]}",
                "customer": data.get('customer', 'Updated Customer'),
                "warehouse": user.profile.warehouse.name if hasattr(user, 'profile') and user.profile.warehouse else 'Unknown',
                "status": data.get('status', 'updated'),
                "items": data.get('items', []),
                "updated_at": "2024-01-17"
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class QuotationDeleteView(generics.DestroyAPIView):
    """
    API view specifically for deleting quotations
    """
    permission_classes = [HasWarehouseAccess]
    
    def get_queryset(self):
        """Return quotations based on user role and warehouse access"""
        user = self.request.user
        
        # If you have a Quotation model, uncomment and modify this:
        # if hasattr(user, "profile") and user.profile.role in ["ceo", "chairman"]:
        #     return Quotation.objects.all()
        # if hasattr(user, "profile") and user.profile.warehouse:
        #     return Quotation.objects.filter(warehouse=user.profile.warehouse)
        # return Quotation.objects.none()
        
        # For now, return empty queryset to prevent errors
        from django.db import models
        return models.QuerySet(model=None)
    
    def destroy(self, request, pk, *args, **kwargs):
        """Delete a specific quotation"""
        user = request.user
        
        # Here you would fetch and delete the quotation
        # try:
        #     quotation = self.get_queryset().get(pk=pk)
        #     quotation_number = quotation.quotation_number
        #     quotation.delete()
        # except Quotation.DoesNotExist:
        #     return Response({'success': False, 'message': 'Quotation not found'}, 
        #                   status=status.HTTP_404_NOT_FOUND)
        
        # For now, return sample response
        response_data = {
            "success": True,
            "message": f"Quotation {str(pk)[:8]} deleted successfully"
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class QuotationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting individual quotations
    """
    permission_classes = [HasWarehouseAccess]
    
    def get_queryset(self):
        """Return quotations based on user role and warehouse access"""
        user = self.request.user
        
        # If you have a Quotation model, uncomment and modify this:
        # if hasattr(user, "profile") and user.profile.role in ["ceo", "chairman"]:
        #     return Quotation.objects.all()
        # if hasattr(user, "profile") and user.profile.warehouse:
        #     return Quotation.objects.filter(warehouse=user.profile.warehouse)
        # return Quotation.objects.none()
        
        # For now, return empty queryset to prevent errors
        from django.db import models
        return models.QuerySet(model=None)
    
    def retrieve(self, request, pk, *args, **kwargs):
        """Get a specific quotation by ID"""
        # Replace with actual model lookup
        sample_quotation = {
            "success": True,
            "quotation": {
                "id": int(pk),
                "quotation_number": f"QUO-{pk:03d}",
                "customer": "Sample Customer",
                "warehouse": "Main Warehouse",
                "items": [
                    {"product": "Chemical A", "quantity": 100, "price": 25.00, "total": 2500.00},
                    {"product": "Chemical B", "quantity": 50, "price": 30.00, "total": 1500.00}
                ],
                "total_amount": 4000.00,
                "status": "pending",
                "created_at": "2024-01-15",
                "notes": "Sample quotation notes"
            }
        }
        return Response(sample_quotation, status=status.HTTP_200_OK)


# ================= QUOTATION FUNCTION-BASED VIEWS ==================
@api_view(['PUT', 'PATCH'])
@permission_classes([HasWarehouseAccess])
def update_quotation_status(request, pk):
    """
    Function-based view to update quotation status
    """
    try:
        data = request.data
        new_status = data.get('status')
        
        if not new_status:
            return Response({
                'success': False,
                'message': 'Status field is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate status values
        valid_statuses = ['draft', 'pending', 'approved', 'rejected', 'expired']
        if new_status not in valid_statuses:
            return Response({
                'success': False,
                'message': f'Invalid status. Valid options: {", ".join(valid_statuses)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check user permissions
        user = request.user
        # Here you would fetch and update the quotation
        # try:
        #     if hasattr(user, "profile") and user.profile.role in ["ceo", "chairman"]:
        #         quotation = Quotation.objects.get(pk=pk)
        #     elif hasattr(user, "profile") and user.profile.warehouse:
        #         quotation = Quotation.objects.get(pk=pk, warehouse=user.profile.warehouse)
        #     else:
        #         return Response({'success': False, 'message': 'Access denied'}, 
        #                       status=status.HTTP_403_FORBIDDEN)
        #     
        #     quotation.status = new_status
        #     quotation.save()
        # except Quotation.DoesNotExist:
        #     return Response({'success': False, 'message': 'Quotation not found'}, 
        #                   status=status.HTTP_404_NOT_FOUND)
        
        # For now, return sample response
        response_data = {
            "success": True,
            "message": f"Quotation status updated to '{new_status}' successfully",
            "quotation": {
                "id": str(pk),
                "quotation_number": f"QUO-{str(pk)[:8]}",
                "status": new_status,
                "updated_at": "2024-01-17",
                "updated_by": user.username
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error updating quotation status: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([HasWarehouseAccess])
def add_quotation_item(request, quotation_id):
    """
    Function-based view to add an item to a quotation
    """
    try:
        data = request.data
        user = request.user
        
        # Required fields validation
        required_fields = ['product_id', 'quantity', 'price']
        for field in required_fields:
            if not data.get(field):
                return Response({
                    'success': False,
                    'message': f'{field.replace("_", " ").title()} is required'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate quantity and price are positive numbers
        try:
            quantity = float(data.get('quantity'))
            price = float(data.get('price'))
            
            if quantity <= 0:
                return Response({
                    'success': False,
                    'message': 'Quantity must be greater than 0'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if price < 0:
                return Response({
                    'success': False,
                    'message': 'Price cannot be negative'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except (ValueError, TypeError):
            return Response({
                'success': False,
                'message': 'Quantity and price must be valid numbers'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check user permissions and quotation access
        # Here you would fetch the quotation and add the item
        # try:
        #     if hasattr(user, "profile") and user.profile.role in ["ceo", "chairman"]:
        #         quotation = Quotation.objects.get(pk=quotation_id)
        #     elif hasattr(user, "profile") and user.profile.warehouse:
        #         quotation = Quotation.objects.get(pk=quotation_id, warehouse=user.profile.warehouse)
        #     else:
        #         return Response({'success': False, 'message': 'Access denied'}, 
        #                       status=status.HTTP_403_FORBIDDEN)
        #     
        #     # Get the product
        #     product = Product.objects.get(pk=data.get('product_id'))
        #     
        #     # Create quotation item
        #     quotation_item = QuotationItem.objects.create(
        #         quotation=quotation,
        #         product=product,
        #         quantity=quantity,
        #         price=price,
        #         total=quantity * price,
        #         notes=data.get('notes', '')
        #     )
        # except Quotation.DoesNotExist:
        #     return Response({'success': False, 'message': 'Quotation not found'}, 
        #                   status=status.HTTP_404_NOT_FOUND)
        # except Product.DoesNotExist:
        #     return Response({'success': False, 'message': 'Product not found'}, 
        #                   status=status.HTTP_404_NOT_FOUND)
        
        # Calculate total
        total = quantity * price
        
        # For now, return sample response
        response_data = {
            "success": True,
            "message": "Item added to quotation successfully",
            "item": {
                "id": f"item-{str(quotation_id)[:8]}-{data.get('product_id')}",
                "quotation_id": str(quotation_id),
                "product_id": data.get('product_id'),
                "product_name": f"Product {data.get('product_id')}",  # Would come from actual product lookup
                "quantity": quantity,
                "price": price,
                "total": total,
                "notes": data.get('notes', ''),
                "added_at": "2024-01-17",
                "added_by": user.username
            }
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error adding item to quotation: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([HasWarehouseAccess])
def quotation_item_detail(request, quotation_id, item_id):
    """
    Function-based view to handle individual quotation items
    GET: Retrieve item details
    PUT/PATCH: Update item
    DELETE: Remove item from quotation
    """
    try:
        user = request.user
        
        # Check user permissions for the quotation
        # Here you would verify access to the quotation and item
        # try:
        #     if hasattr(user, "profile") and user.profile.role in ["ceo", "chairman"]:
        #         quotation = Quotation.objects.get(pk=quotation_id)
        #         quotation_item = QuotationItem.objects.get(pk=item_id, quotation=quotation)
        #     elif hasattr(user, "profile") and user.profile.warehouse:
        #         quotation = Quotation.objects.get(pk=quotation_id, warehouse=user.profile.warehouse)
        #         quotation_item = QuotationItem.objects.get(pk=item_id, quotation=quotation)
        #     else:
        #         return Response({'success': False, 'message': 'Access denied'}, 
        #                       status=status.HTTP_403_FORBIDDEN)
        # except (Quotation.DoesNotExist, QuotationItem.DoesNotExist):
        #     return Response({'success': False, 'message': 'Quotation or item not found'}, 
        #                   status=status.HTTP_404_NOT_FOUND)
        
        if request.method == 'GET':
            # Get item details
            sample_item = {
                "id": str(item_id),
                "quotation_id": str(quotation_id),
                "product_id": "123",
                "product_name": "Sample Chemical Product",
                "product_formula": "H2SO4",
                "quantity": 50,
                "price": 25.99,
                "total": 1299.50,
                "notes": "Sample item notes",
                "created_at": "2024-01-15",
                "updated_at": "2024-01-17"
            }
            
            return Response({
                'success': True,
                'item': sample_item
            }, status=status.HTTP_200_OK)
        
        elif request.method in ['PUT', 'PATCH']:
            # Update item
            data = request.data
            
            # Validate numeric fields if provided
            if 'quantity' in data:
                try:
                    quantity = float(data['quantity'])
                    if quantity <= 0:
                        return Response({
                            'success': False,
                            'message': 'Quantity must be greater than 0'
                        }, status=status.HTTP_400_BAD_REQUEST)
                except (ValueError, TypeError):
                    return Response({
                        'success': False,
                        'message': 'Quantity must be a valid number'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            if 'price' in data:
                try:
                    price = float(data['price'])
                    if price < 0:
                        return Response({
                            'success': False,
                            'message': 'Price cannot be negative'
                        }, status=status.HTTP_400_BAD_REQUEST)
                except (ValueError, TypeError):
                    return Response({
                        'success': False,
                        'message': 'Price must be a valid number'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Here you would update the quotation item
            # for field, value in data.items():
            #     if hasattr(quotation_item, field):
            #         setattr(quotation_item, field, value)
            # quotation_item.total = quotation_item.quantity * quotation_item.price
            # quotation_item.save()
            
            updated_item = {
                "id": str(item_id),
                "quotation_id": str(quotation_id),
                "product_id": data.get('product_id', '123'),
                "product_name": "Updated Chemical Product",
                "quantity": data.get('quantity', 50),
                "price": data.get('price', 25.99),
                "total": float(data.get('quantity', 50)) * float(data.get('price', 25.99)),
                "notes": data.get('notes', 'Updated notes'),
                "updated_at": "2024-01-17",
                "updated_by": user.username
            }
            
            return Response({
                'success': True,
                'message': 'Item updated successfully',
                'item': updated_item
            }, status=status.HTTP_200_OK)
        
        elif request.method == 'DELETE':
            # Delete item
            # quotation_item.delete()
            
            return Response({
                'success': True,
                'message': f'Item {str(item_id)[:8]} removed from quotation successfully'
            }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error handling quotation item: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ================= APP VIEWS ==================
class MyModelListCreateView(generics.ListCreateAPIView):
    serializer_class = MyModelSerializer
    permission_classes = [HasWarehouseAccess]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "profile") and user.profile.role in ["ceo", "chairman"]:
            return MyModel.objects.all()
        if hasattr(user, "profile") and user.profile.warehouse:
            return MyModel.objects.filter(warehouse=user.profile.warehouse)
        return MyModel.objects.none()


class MyModelDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MyModelSerializer
    permission_classes = [HasWarehouseAccess]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "profile") and user.profile.role in ["ceo", "chairman"]:
            return MyModel.objects.all()
        if hasattr(user, "profile") and user.profile.warehouse:
            return MyModel.objects.filter(warehouse=user.profile.warehouse)
        return MyModel.objects.none()


class ProductListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [HasWarehouseAccess]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "profile") and user.profile.role in ["ceo", "chairman"]:
            return Product.objects.all()
        if hasattr(user, "profile") and user.profile.warehouse:
            return Product.objects.filter(warehouse=user.profile.warehouse)
        return Product.objects.none()


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer
    permission_classes = [HasWarehouseAccess]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "profile") and user.profile.role in ["ceo", "chairman"]:
            return Product.objects.all()
        if hasattr(user, "profile") and user.profile.warehouse:
            return Product.objects.filter(warehouse=user.profile.warehouse)
        return Product.objects.none()