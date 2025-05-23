import logging
from django.http import HttpResponse # JsonResponse no se usa, se puede quitar si quieres
from django.db import connection, OperationalError
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import UserCreateForm

# --- CORREGIDO: Usar doble guion bajo para _name_ ---
logger = logging.getLogger(__name__)

# --- MANTENIDO: Funciones para las sondas ---
def readiness_check(request):
    """
    /health/ready: Usada por Startup Probe. Verifica conexión a BD.
    """
    db_ready = False
    try:
        # Intenta una consulta simple a la BD
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_ready = True
        logger.info("Startup/Readiness probe: Database connection successful.") # Log de éxito
    except Exception as e:
        # Loguea el error si la conexión falla
        logger.error(f"Startup/Readiness probe - DB connection error: {e}")
        db_ready = False

    # is_ready será True solo si db_ready es True
    is_ready = db_ready

    if is_ready:
        # Devuelve 200 OK si la BD está lista
        return HttpResponse("Ready", status=200, content_type="text/plain")
    else:
        # Devuelve 503 si la BD no está lista (o hubo otro error)
        return HttpResponse("Unavailable", status=503, content_type="text/plain")

def liveness_check(request):
    """
    /health/live: Usada por Liveness Probe. Verifica que el proceso responde.
    """
    # Simplemente devuelve 200 OK para indicar que el proceso está vivo.
    logger.debug("Liveness probe successful.") # Log opcional
    return HttpResponse("Alive", status=200, content_type="text/plain")

# User management views for admin users

def is_admin(user):
    """Check if the user is an admin (has staff status or is in admin group)"""
    return user.is_staff or user.is_superuser or user.groups.filter(name='admin').exists()

@login_required
@user_passes_test(is_admin)
def user_list(request):
    """View to list all users - accessible only to admin users"""
    from django.contrib.auth.models import User
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'core/user_list.html', {'users': users})

@login_required
@user_passes_test(is_admin)
def user_create(request):
    """View to create a new user - accessible only to admin users"""
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Usuario "{user.username}" creado exitosamente.')
            return redirect('user_list')
        else:
            # Log form errors for debugging
            print(f"Form is invalid. Errors: {form.errors}")
            messages.error(request, 'Error al crear usuario. Por favor corrija los errores indicados.')
    else:
        form = UserCreateForm()

    return render(request, 'core/user_create.html', {'form': form})
