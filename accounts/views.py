from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import DatosUsuarioForm, PerfilForm, RegistroForm
from .models import Perfil


def registro(request):
    if request.user.is_authenticated:
        return redirect('perfil')

    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            Perfil.objects.create(user=usuario)
            login(request, usuario)
            messages.success(request, f"Bienvenido, {usuario.username}. Tu cuenta se creó correctamente.")
            return redirect('perfil')
    else:
        form = RegistroForm()

    return render(request, 'accounts/registro.html', {'form': form})


@login_required(login_url='login')
def perfil(request):
    perfil_usuario, _ = Perfil.objects.get_or_create(user=request.user)
    return render(request, 'accounts/perfil.html', {'perfil': perfil_usuario})


@login_required(login_url='login')
def editar_perfil(request):
    perfil_usuario, _ = Perfil.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form_perfil = PerfilForm(request.POST, request.FILES, instance=perfil_usuario)
        form_usuario = DatosUsuarioForm(request.POST, instance=request.user)
        if form_perfil.is_valid() and form_usuario.is_valid():
            form_perfil.save()
            form_usuario.save()
            messages.success(request, "Perfil actualizado.")
            return redirect('perfil')
    else:
        form_perfil = PerfilForm(instance=perfil_usuario)
        form_usuario = DatosUsuarioForm(instance=request.user)

    return render(request, 'accounts/editar_perfil.html', {
        'form_perfil': form_perfil,
        'form_usuario': form_usuario,
    })
