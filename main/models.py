from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
import random
import string

class Rifa(models.Model):
    ESTADO_CHOICES = [
        ('activa', 'Activa'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
        ('sorteada', 'Sorteada'),
    ]
    
    nombre = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    descripcion = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_sorteo = models.DateTimeField()
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    precio_numero = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    cantidad_numeros = models.PositiveIntegerField(
        default=100,
        validators=[MinValueValidator(1), MaxValueValidator(100000)]
    )
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default='activa'
    )
    premio_principal = models.TextField(blank=True, null=True)
    imagen = models.ImageField(
        upload_to='rifas/', 
        blank=True, 
        null=True
    )
    numeros_por_usuario = models.PositiveIntegerField(
        default=10,
        validators=[MinValueValidator(1)],
        help_text="Máximo de números que un usuario puede comprar"
    )
    numeros_generados = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Rifa'
        verbose_name_plural = 'Rifas'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['estado', 'fecha_sorteo']),
            models.Index(fields=['fecha_sorteo']),
        ]
    
    def __str__(self):
        return self.nombre
    
    def generar_numeros(self):
        """Genera los números automáticamente para la rifa"""
        if not self.numeros_generados:
            numeros_a_crear = []
            for numero in range(1, self.cantidad_numeros + 1):
                numeros_a_crear.append(
                    Numero(
                        rifa=self,
                        numero=numero,
                        estado='disponible'
                    )
                )
            # Crear todos los números en lote para mejor rendimiento
            Numero.objects.bulk_create(numeros_a_crear)
            self.numeros_generados = True
            self.save()
    
    @property
    def numeros_vendidos(self):
        return self.numeros.filter(estado='vendido').count()
    
    @property
    def numeros_disponibles(self):
        return self.cantidad_numeros - self.numeros_vendidos
    
    @property
    def porcentaje_vendido(self):
        if self.cantidad_numeros == 0:
            return 0
        return (self.numeros_vendidos / self.cantidad_numeros) * 100
    
    @property
    def esta_activa(self):
        return self.estado == 'activa' and timezone.now() < self.fecha_sorteo
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)


# Signal para generar números automáticamente después de crear una rifa
@receiver(post_save, sender=Rifa)
def generar_numeros_rifa(sender, instance, created, **kwargs):
    if created and not instance.numeros_generados:
        instance.generar_numeros()


class Numero(models.Model):
    ESTADO_CHOICES = [
        ('disponible', 'Disponible'),
        ('reservado', 'Reservado'),
        ('vendido', 'Vendido'),
    ]
    
    rifa = models.ForeignKey(
        Rifa, 
        on_delete=models.CASCADE, 
        related_name='numeros'
    )
    numero = models.PositiveIntegerField()
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default='disponible'
    )
    fecha_reserva = models.DateTimeField(blank=True, null=True)
    fecha_compra = models.DateTimeField(blank=True, null=True)
    telefono_comprador = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name="Teléfono del comprador"
    )
    nombre_comprador = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Nombre del comprador"
    )
    
    class Meta:
        verbose_name = 'Número'
        verbose_name_plural = 'Números'
        unique_together = ['rifa', 'numero']
        ordering = ['rifa', 'numero']
        indexes = [
            models.Index(fields=['rifa', 'estado']),
            models.Index(fields=['telefono_comprador']),
        ]
    
    def __str__(self):
        return f"Rifa {self.rifa.nombre} - Número {self.numero}"
    
    @property
    def vendido(self):
        return self.estado == 'vendido'
    
    @property
    def disponible(self):
        return self.estado == 'disponible'
    
    @property
    def reservado(self):
        return self.estado == 'reservado'


class Transaccion(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
        ('rechazada', 'Rechazada'),
    ]
    
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('tarjeta', 'Tarjeta'),
        ('otros', 'Otros'),
    ]
    
    telefono_cliente = models.CharField(
        max_length=20,
        verbose_name="Teléfono del cliente"
    )
    nombre_cliente = models.CharField(
        max_length=100,
        verbose_name="Nombre del cliente"
    )
    rifa = models.ForeignKey(
        Rifa,
        on_delete=models.CASCADE,
        related_name='transacciones'
    )
    numeros = models.ManyToManyField(Numero, related_name='transacciones')
    cantidad_numeros = models.PositiveIntegerField(
        default=0,
        editable=False  # Se calcula automáticamente
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    monto_total = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        editable=False  # Se calcula automáticamente
    )
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default='pendiente'
    )
    codigo_transaccion = models.CharField(
        max_length=50, 
        unique=True,
        blank=True
    )
    metodo_pago = models.CharField(
        max_length=20, 
        choices=METODO_PAGO_CHOICES, 
        default='efectivo'
    )
    notas = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Transacción'
        verbose_name_plural = 'Transacciones'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['telefono_cliente', 'estado']),
            models.Index(fields=['codigo_transaccion']),
        ]
    
    def __str__(self):
        return f"Transacción {self.codigo_transaccion} - {self.nombre_cliente}"
    
    def calcular_monto_total(self):
        """Calcula el monto total basado en la cantidad de números y el precio de la rifa"""
        if hasattr(self, 'rifa') and self.rifa:
            return self.cantidad_numeros * self.rifa.precio_numero
        return 0
    
    def save(self, *args, **kwargs):
        # Generar código de transacción si no existe
        if not self.codigo_transaccion:
            self.codigo_transaccion = self.generar_codigo_transaccion()
        
        # Calcular monto total automáticamente
        self.monto_total = self.calcular_monto_total()
        
        # Llamar al save original
        super().save(*args, **kwargs)
        
        # Actualizar cantidad_numeros después de guardar (para ManyToMany)
        if self.pk:
            self.cantidad_numeros = self.numeros.count()
            # Guardar nuevamente para actualizar cantidad_numeros
            if self.cantidad_numeros != self.numeros.count():
                super().save(update_fields=['cantidad_numeros', 'monto_total'])
    
    def generar_codigo_transaccion(self):
        """Genera un código único para la transacción"""
        import random
        import string
        prefix = 'TXN'
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return f"{prefix}{random_str}"
    
    def marcar_numeros_como_vendidos(self):
        """Marca los números asociados como vendidos y actualiza la información del comprador"""
        for numero in self.numeros.all():
            numero.estado = 'vendido'
            numero.telefono_comprador = self.telefono_cliente
            numero.nombre_comprador = self.nombre_cliente
            numero.fecha_compra = timezone.now()
            numero.save()
class Ganador(models.Model):
    rifa = models.OneToOneField(
        Rifa,
        on_delete=models.CASCADE,
        related_name='ganador'
    )
    numero_ganador = models.ForeignKey(
        Numero,
        on_delete=models.CASCADE,
        related_name='premios_ganados'
    )
    fecha_anuncio = models.DateTimeField(auto_now_add=True)
    premio_entregado = models.BooleanField(default=False)
    fecha_entrega = models.DateTimeField(blank=True, null=True)
    telefono_ganador = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Teléfono del ganador"
    )
    nombre_ganador = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Nombre del ganador"
    )
    
    class Meta:
        verbose_name = 'Ganador'
        verbose_name_plural = 'Ganadores'
    
    def __str__(self):
        return f"Ganador de {self.rifa.nombre} - Número {self.numero_ganador.numero}"
    
    def save(self, *args, **kwargs):
        # Actualizar información del ganador desde el número
        if self.numero_ganador and self.numero_ganador.telefono_comprador:
            self.telefono_ganador = self.numero_ganador.telefono_comprador
            self.nombre_ganador = self.numero_ganador.nombre_comprador
        super().save(*args, **kwargs)