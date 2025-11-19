from django.urls import path
from .views import *
urlpatterns = [
    path('', home_view, name='home'),
    path('mis-rifas/', mis_rifas_view, name='mis_rifas'),
]
