from django.contrib import admin
from .models import Rifa, Numero, Transaccion, Ganador

@admin.register(Rifa)
class RifaAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 
        'estado', 
        'precio_numero', 
        'numeros_vendidos',
        'cantidad_numeros',
        'fecha_sorteo',
        'esta_activa'
    ]
    list_filter = ['estado', 'fecha_sorteo', 'fecha_creacion']
    search_fields = ['nombre', 'descripcion']
    prepopulated_fields = {'slug': ('nombre',)}
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion', 'numeros_vendidos', 'porcentaje_vendido']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'slug', 'descripcion', 'imagen')
        }),
        ('Configuración', {
            'fields': (
                'precio_numero', 
                'cantidad_numeros', 
                'numeros_por_usuario',
                'premio_principal'
            )
        }),
        ('Fechas y Estado', {
            'fields': (
                'fecha_sorteo', 
                'estado',
                'fecha_creacion',
                'fecha_actualizacion'
            )
        }),
        ('Estadísticas', {
            'fields': (
                'numeros_vendidos',
                'numeros_disponibles',
                'porcentaje_vendido',
                'esta_activa'
            )
        })
    )

@admin.register(Numero)
class NumeroAdmin(admin.ModelAdmin):
    list_display = [
        'numero', 
        'rifa', 
        'estado', 
        'comprador',
        'fecha_compra'
    ]
    list_filter = ['estado', 'rifa', 'fecha_compra']
    search_fields = ['numero', 'comprador__username', 'rifa__nombre']
    readonly_fields = ['fecha_reserva', 'fecha_compra']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('rifa', 'comprador')

@admin.register(Transaccion)
class TransaccionAdmin(admin.ModelAdmin):
    list_display = [
        'codigo_transaccion',
        'usuario',
        'rifa',
        'monto_total',
        'estado',
        'fecha_creacion'
    ]
    list_filter = ['estado', 'fecha_creacion', 'metodo_pago']
    search_fields = ['codigo_transaccion', 'usuario__username', 'rifa__nombre']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('usuario', 'rifa')

@admin.register(Ganador)
class GanadorAdmin(admin.ModelAdmin):
    list_display = [
        'rifa',
        'numero_ganador',
        'premio_entregado',
        'fecha_anuncio'
    ]
    list_filter = ['premio_entregado', 'fecha_anuncio']
    search_fields = ['rifa__nombre', 'numero_ganador__numero']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('rifa', 'numero_ganador')