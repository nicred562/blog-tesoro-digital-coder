from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm
from .models import Post


def inicio(request):
    posts_destacados = Post.objects.filter(estado=Post.Estado.PUBLICADO).order_by("-fecha_creacion")[:3]
    return render(request, 'posts/inicio.html', {'posts_destacados': posts_destacados})


def acerca(request):
    return render(request, 'posts/acerca.html')


def ayuda(request):
    return render(request, 'posts/ayuda.html')


def terminos(request):
    return render(request, 'posts/terminos.html')


def contacto(request):
    return render(request, 'posts/contacto.html')


def lista_posts(request):
    posts = Post.objects.filter(estado="publicado").order_by("-fecha_creacion")
    context = {
        "posts": posts
    }
    return render(request, "posts/lista_posts.html", context)


def detalle_post(request, slug):
    post = get_object_or_404(Post, slug=slug, estado=Post.Estado.PUBLICADO)
    return render(request, 'posts/detalle_post.html', {'post': post})


def gestionar_posts(request):
    """Listado con TODOS los posts (cualquier estado), para crear/editar/borrar."""
    posts = Post.objects.all()
    return render(request, 'posts/gestionar_posts.html', {'posts': posts})


def crear_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save()
            messages.success(request, f"Post '{post.titulo}' creado.")
            return redirect('gestionar_posts')
    else:
        form = PostForm()

    return render(request, 'posts/post_form.html', {'form': form, 'titulo_pagina': 'Nueva nota'})


def editar_post(request, slug):
    post = get_object_or_404(Post, slug=slug)

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, f"Post '{post.titulo}' actualizado.")
            return redirect('gestionar_posts')
    else:
        form = PostForm(instance=post)

    return render(request, 'posts/post_form.html', {'form': form, 'post': post, 'titulo_pagina': 'Editar nota'})


def eliminar_post(request, slug):
    post = get_object_or_404(Post, slug=slug)

    if request.method == 'POST':
        titulo = post.titulo
        post.delete()
        messages.info(request, f"Post '{titulo}' eliminado.")
        return redirect('gestionar_posts')

    return render(request, 'posts/post_confirm_delete.html', {'post': post})
