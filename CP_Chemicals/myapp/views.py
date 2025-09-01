# myapp/views.py
from django.shortcuts import render
from rest_framework import generics
from .models import MyModel
from .serializers import MyModelSerializer
from .permissions import HasWarehouseAccess # Import the custom permission

# Django View for a traditional web page
def home(request):
    return render(request, 'myapp/home.html')

# Django REST Framework View for an API endpoint
class MyModelListCreateView(generics.ListCreateAPIView):
    serializer_class = MyModelSerializer
    permission_classes = [HasWarehouseAccess] # Apply the new custom permission

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