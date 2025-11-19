from django.core.paginator import Paginator
from django.shortcuts import render
from django.db.models import Count, Sum, F, Q
from django.contrib.auth.decorators import login_required
from .models import Rifa

@login_required
def mis_rifas_view(request):
    # Obtener parámetros de la URL
    page_number = request.GET.get('page', 1)
    sort_by = request.GET.get('sort', '-fecha_creacion')
    filter_estado = request.GET.get('estado', 'all')
    search_query = request.GET.get('q', '')
    
    # Base queryset
    rifas = Rifa.objects.all()
    
    # Aplicar búsqueda
    if search_query:
        rifas = rifas.filter(
            Q(nombre__icontains=search_query) |
            Q(descripcion__icontains=search_query)
        )
    
    # Aplicar filtro por estado si no es 'all'
    if filter_estado != 'all':
        rifas = rifas.filter(estado=filter_estado)
    
    # Aplicar ordenamiento
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