# myapp/admin.py
from django.contrib import admin
from .models import MyModel, Profile

admin.site.register(MyModel)
admin.site.register(Profile)