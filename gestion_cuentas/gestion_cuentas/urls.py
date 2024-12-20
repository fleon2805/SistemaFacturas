"""
URL configuration for gestion_cuentas project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from cuentas.views import CustomTokenObtainPairView  # Importa la vista personalizada
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),  # Rutas del panel de administración
    path('api/', include('cuentas.urls')),  # Incluir las rutas de la app 'cuentas'
    
    # Endpoints de JWT
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),  # Token de obtención personalizado
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Token de refresco
]
