from django.http import Http404
from django.shortcuts import render

from .datos import obtener_post, obtener_posts


def inicio(request):
    return render(request, 'posts/inicio.html', {'posts_destacados': obtener_posts()[:3]})


def acerca(request):
    return render(request, 'posts/acerca.html')


def ayuda(request):
    return render(request, 'posts/ayuda.html')


def terminos(request):
    return render(request, 'posts/terminos.html')


def lista_posts(request):
    return render(request, 'posts/lista_posts.html', {'posts': obtener_posts()})


def detalle_post(request, slug):
    post = obtener_post(slug)
    if post is None:
        raise Http404("Ese post no existe.")
    return render(request, 'posts/detalle_post.html', {'post': post})
