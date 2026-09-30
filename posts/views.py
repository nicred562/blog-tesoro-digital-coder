from django.shortcuts import get_object_or_404, render

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
