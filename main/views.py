from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Rifa, Numero, Transaccion

@login_required
def mis_rifas_view(request):
    page_number = request.GET.get('page', 1)
    sort_by = request.GET.get('sort', '-fecha_creacion')
    filter_estado = request.GET.get('estado', 'all')
    search_query = request.GET.get('q', '')
    
    rifas = Rifa.objects.all()
    
    if search_query:
        rifas = rifas.filter(
            Q(nombre__icontains=search_query) |
            Q(descripcion__icontains=search_query)
        )
    
    if filter_estado != 'all':
        rifas = rifas.filter(estado=filter_estado)
    
    valid_sorts = {
        '-fecha_creacion': 'Más recientes',
        'fecha_creacion': 'Más antiguas',
        'nombre': 'Nombre A-Z',
        '-nombre': 'Nombre Z-A', 
        'fecha_sorteo': 'Sorteo próximo',
        '-fecha_sorteo': 'Sorteo lejano',
        '-numeros_vendidos': 'Más vendidas',
        'numeros_vendidos': 'Menos vendidas'
    }
    
    if sort_by in valid_sorts:
        rifas = rifas.order_by(sort_by)
    else:
        rifas = rifas.order_by('-fecha_creacion')
    
    # Paginación
    paginator = Paginator(rifas, 12)
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_rifas = Rifa.objects.count()
    rifas_activas = Rifa.objects.filter(estado='activa').count()
    rifas_completadas = Rifa.objects.filter(estado='completada').count()
    
    context = {
        'rifas': page_obj,
        'total_rifas': total_rifas,
        'rifas_activas': rifas_activas,
        'rifas_completadas': rifas_completadas,
        'current_sort': sort_by,
        'current_filter': filter_estado,
        'search_query': search_query,
        'sort_options': valid_sorts,
    }
    
    return render(request, 'mis_rifas.html', context)

def home_view(request):
    return render(request, 'home.html')

@login_required
def gestion_numeros_rifa(request, rifa_id):
    rifa = get_object_or_404(Rifa, id=rifa_id)
    
    # Obtener parámetros
    page = request.GET.get('page', 1)
    filter_estado = request.GET.get('estado', 'all')
    search_numero = request.GET.get('numero', '')
    
    # Filtrar números
    numeros = Numero.objects.filter(rifa=rifa)
    
    if filter_estado != 'all':
        numeros = numeros.filter(estado=filter_estado)
    
    if search_numero:
        numeros = numeros.filter(numero=search_numero)
    
    # Paginación
    numeros = numeros.order_by('numero')
    
    # Estadísticas
    stats = {
        'total': numeros.count(),
        'disponibles': numeros.filter(estado='disponible').count(),
        'reservados': numeros.filter(estado='reservado').count(),
        'vendidos': numeros.filter(estado='vendido').count(),
    }
    
    context = {
        'rifa': rifa,
        'numeros': numeros,
        'stats': stats,
        'current_filter': filter_estado,
        'search_numero': search_numero,
    }
    
    return render(request, 'gestion_numeros.html', context)

@login_required

@require_POST
def actualizar_estado_numero(request, numero_id):
    numero = get_object_or_404(Numero, id=numero_id)
    nuevo_estado = request.POST.get('estado')
    telefono = request.POST.get('telefono', '')
    nombre = request.POST.get('nombre', '')
    
    if nuevo_estado in ['disponible', 'reservado', 'vendido']:
        numero.estado = nuevo_estado
        numero.telefono_comprador = telefono if telefono else None
        numero.nombre_comprador = nombre if nombre else None
        
        if nuevo_estado == 'vendido':
            numero.fecha_compra = timezone.now()
        elif nuevo_estado == 'reservado':
            numero.fecha_reserva = timezone.now()
        elif nuevo_estado == 'disponible':
            numero.fecha_reserva = None
            numero.fecha_compra = None
            numero.telefono_comprador = None
            numero.nombre_comprador = None
        
        numero.save()
        
        return JsonResponse({
            'success': True,
            'numero': numero.numero,
            'estado': numero.estado,
            'estado_display': numero.get_estado_display()
        })
    
    return JsonResponse({'success': False, 'error': 'Estado inválido'})

@login_required
def obtener_datos_numero(request, numero_id):
    numero = get_object_or_404(Numero, id=numero_id)
    
    return JsonResponse({
        'numero': numero.numero,
        'estado': numero.estado,
        'telefono_comprador': numero.telefono_comprador or '',
        'nombre_comprador': numero.nombre_comprador or '',
        'fecha_reserva': numero.fecha_reserva.isoformat() if numero.fecha_reserva else '',
        'fecha_compra': numero.fecha_compra.isoformat() if numero.fecha_compra else '',
    })
