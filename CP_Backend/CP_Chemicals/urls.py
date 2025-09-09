# CP_Chemicals/urls.py
# your_project/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,  # This line is for the logout view
)

urlpatterns = [
    # These paths are for JWT token authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # This is the new path for logging out.
    path('api/token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),

    # This path includes all URLs from your 'myapp', including both API and traditional views
    path('', include('myapp.urls')),
    
    # This path routes to the Django admin panel.
    path('admin/', admin.site.urls),
    
    # This path provides the browsable login/logout views for the API.
    path('api-auth/', include('rest_framework.urls'))
]