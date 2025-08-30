# myapp/views.py

from django.shortcuts import render
from rest_framework import generics
from .models import MyModel
from .serializers import MyModelSerializer

# Django View for a traditional web page
def home(request):
    return render(request, 'myapp/home.html')

# Django REST Framework View for an API endpoint
class MyModelListCreateView(generics.ListCreateAPIView):
    queryset = MyModel.objects.all()
    serializer_class = MyModelSerializer