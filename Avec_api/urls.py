from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('Api_Avec_App.urls')),
    
    # --- Swagger & OpenAPI Schema ---
    # Génère le schéma JSON/YAML
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    
    # Interface Swagger UI
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # Interface Redoc (optionnel)
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]