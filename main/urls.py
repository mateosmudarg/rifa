from django.urls import path
from .views import *
urlpatterns = [
    path('', home_view, name='home'),
    path('mis-rifas/', mis_rifas_view, name='mis_rifas'),
    path('rifa/<int:rifa_id>/numeros/', gestion_numeros_rifa, name='gestion_numeros'),
    path('numero/<int:numero_id>/actualizar/', actualizar_estado_numero, name='actualizar_estado_numero'),
    path('numero/<int:numero_id>/datos/', obtener_datos_numero, name='obtener_datos_numero'),

]
