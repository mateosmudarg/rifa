from django.contrib import admin
from django import forms
from .models import Rifa, Numero, Transaccion, Ganador

class TransaccionForm(forms.ModelForm):
    class Meta:
        model = Transaccion
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar números disponibles solo si hay una rifa seleccionada
        if 'rifa' in self.data:
            try:
                rifa_id = int(self.data.get('rifa'))
                self.fields['numeros'].queryset = Numero.objects.filter(
                    rifa_id=rifa_id, 
                    estado='disponible'
                ).order_by('numero')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.rifa:
            self.fields['numeros'].queryset = Numero.objects.filter(
                rifa=self.instance.rifa, 
                estado='disponible'
            ).order_by('numero')
        else:
            # Si no hay rifa seleccionada, mostrar números vacíos
            self.fields['numeros'].queryset = Numero.objects.none()

@admin.register(Rifa)
class RifaAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 
        'estado', 
        'precio_numero', 
        'get_numeros_vendidos',
        'cantidad_numeros',
        'fecha_sorteo',
        'get_esta_activa',
        'numeros_generados'
    ]
    list_filter = ['estado', 'fecha_sorteo', 'fecha_creacion', 'numeros_generados']
    search_fields = ['nombre', 'descripcion']
    prepopulated_fields = {'slug': ('nombre',)}
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion', 'numeros_generados']
    actions = ['regenerar_numeros']
    
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
                'fecha_actualizacion',
                'numeros_generados'
            )
        })
    )

    def get_numeros_vendidos(self, obj):
        return obj.numeros_vendidos
    get_numeros_vendidos.short_description = 'Números Vendidos'

    def get_esta_activa(self, obj):
        return obj.esta_activa
    get_esta_activa.short_description = '¿Está Activa?'
    get_esta_activa.boolean = True

    def regenerar_numeros(self, request, queryset):
        """Acción para regenerar números de rifas seleccionadas"""
        for rifa in queryset:
            # Eliminar números existentes
            rifa.numeros.all().delete()
            rifa.numeros_generados = False
            rifa.save()
            # Generar nuevos números
            rifa.generar_numeros()
        self.message_user(request, f"Se regeneraron los números para {queryset.count()} rifa(s)")
    regenerar_numeros.short_description = "Regenerar números para las rifas seleccionadas"

@admin.register(Numero)
class NumeroAdmin(admin.ModelAdmin):
    list_display = [
        'numero', 
        'rifa', 
        'estado', 
        'telefono_comprador',
        'nombre_comprador',
        'fecha_compra'
    ]
    list_filter = ['estado', 'rifa', 'fecha_compra']
    search_fields = ['numero', 'telefono_comprador', 'nombre_comprador', 'rifa__nombre']
    readonly_fields = ['fecha_reserva', 'fecha_compra']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('rifa')

@admin.register(Transaccion)
class TransaccionAdmin(admin.ModelAdmin):
    form = TransaccionForm
    list_display = [
        'codigo_transaccion',
        'nombre_cliente',
        'telefono_cliente',
        'rifa',
        'get_cantidad_numeros',
        'monto_total',
        'estado',
        'metodo_pago',
        'fecha_creacion'
    ]
    list_filter = ['estado', 'fecha_creacion', 'metodo_pago', 'rifa']
    search_fields = ['codigo_transaccion', 'nombre_cliente', 'telefono_cliente', 'rifa__nombre']
    readonly_fields = [
        'fecha_creacion', 
        'fecha_actualizacion', 
        'monto_total', 
        'codigo_transaccion',
        'get_cantidad_numeros_display',
        'get_precio_por_numero',
        'get_monto_calculado'
    ]
    
    fieldsets = (
        ('Información del Cliente', {
            'fields': ('nombre_cliente', 'telefono_cliente')
        }),
        ('Detalles de la Transacción', {
            'fields': (
                'rifa', 
                'numeros', 
                'get_cantidad_numeros_display',
                'get_precio_por_numero',
                'monto_total',
                'get_monto_calculado'
            )
        }),
        ('Información de Pago', {
            'fields': ('estado', 'metodo_pago', 'codigo_transaccion', 'notas')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion')
        })
    )
    
    def get_cantidad_numeros(self, obj):
        return obj.numeros.count()
    get_cantidad_numeros.short_description = 'Cantidad de Números'
    
    def get_cantidad_numeros_display(self, obj):
        if obj.pk:
            count = obj.numeros.count()
            return f"{count} número(s)"
        return "Seleccione números primero"
    get_cantidad_numeros_display.short_description = 'Cantidad de Números'
    
    def get_precio_por_numero(self, obj):
        if obj.rifa:
            return f"${obj.rifa.precio_numero} por número"
        return "Seleccione una rifa primero"
    get_precio_por_numero.short_description = 'Precio por Número'
    
    def get_monto_calculado(self, obj):
        if obj.rifa and obj.pk:
            count = obj.numeros.count()
            total = count * obj.rifa.precio_numero
            return f"${total} ({count} × ${obj.rifa.precio_numero})"
        return "El monto se calculará automáticamente"
    get_monto_calculado.short_description = 'Cálculo del Monto'
    
    def save_model(self, request, obj, form, change):
        # Guardar primero para tener el ID
        super().save_model(request, obj, form, change)
        
        # Actualizar la cantidad de números y monto total
        obj.cantidad_numeros = obj.numeros.count()
        obj.monto_total = obj.calcular_monto_total()
        obj.save()
        
        # Si la transacción se marca como completada, marcar los números como vendidos
        if obj.estado == 'completada':
            obj.marcar_numeros_como_vendidos()
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('rifa')
    
    def get_form(self, request, obj=None, **kwargs):
        # Para nuevas transacciones, establecer algunos valores por defecto
        form = super().get_form(request, obj, **kwargs)
        if not obj:
            form.base_fields['estado'].initial = 'pendiente'
            form.base_fields['metodo_pago'].initial = 'efectivo'
        return form

@admin.register(Ganador)
class GanadorAdmin(admin.ModelAdmin):
    list_display = [
        'rifa',
        'numero_ganador',
        'nombre_ganador',
        'telefono_ganador',
        'premio_entregado',
        'fecha_anuncio'
    ]
    list_filter = ['premio_entregado', 'fecha_anuncio']
    search_fields = ['rifa__nombre', 'numero_ganador__numero', 'nombre_ganador', 'telefono_ganador']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('rifa', 'numero_ganador')