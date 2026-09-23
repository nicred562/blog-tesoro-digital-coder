from django.urls import path

from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('acerca/', views.acerca, name='acerca'),
    path('notas/', views.lista_posts, name='lista_posts'),
    path('notas/<slug:slug>/', views.detalle_post, name='detalle_post'),
    path('ayuda/', views.ayuda, name='ayuda'),
    path('terminos/', views.terminos, name='terminos'),
]
