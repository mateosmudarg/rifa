from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth.models import User

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
    
    @property
    def numeros_vendidos(self):
        return self.numeros.filter(vendido=True).count()
    
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
    comprador = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='numeros_comprados'
    )
    
    class Meta:
        verbose_name = 'Número'
        verbose_name_plural = 'Números'
        unique_together = ['rifa', 'numero']
        ordering = ['rifa', 'numero']
        indexes = [
            models.Index(fields=['rifa', 'estado']),
            models.Index(fields=['comprador']),
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
    
    usuario = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='transacciones'
    )
    rifa = models.ForeignKey(
        Rifa,
        on_delete=models.CASCADE,
        related_name='transacciones'
    )
    numeros = models.ManyToManyField(Numero, related_name='transacciones')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
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
    metodo_pago = models.CharField(max_length=50, blank=True)
    
    class Meta:
        verbose_name = 'Transacción'
        verbose_name_plural = 'Transacciones'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['usuario', 'estado']),
            models.Index(fields=['codigo_transaccion']),
        ]
    
    def __str__(self):
        return f"Transacción {self.codigo_transaccion} - {self.usuario.username}"


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
    
    class Meta:
        verbose_name = 'Ganador'
        verbose_name_plural = 'Ganadores'
    
    def __str__(self):
        return f"Ganador de {self.rifa.nombre} - Número {self.numero_ganador.numero}"