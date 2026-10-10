from django.urls import path

from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('acerca/', views.acerca, name='acerca'),
    path('ayuda/', views.ayuda, name='ayuda'),
    path('terminos/', views.terminos, name='terminos'),
    path('contacto/', views.contacto, name='contacto'),

    path('notas/', views.lista_posts, name='lista_posts'),
    path('notas/gestionar/', views.gestionar_posts, name='gestionar_posts'),
    path('notas/crear/', views.crear_post, name='crear_post'),
    path('notas/<slug:slug>/editar/', views.editar_post, name='editar_post'),
    path('notas/<slug:slug>/eliminar/', views.eliminar_post, name='eliminar_post'),
    path('notas/<slug:slug>/', views.detalle_post, name='detalle_post'),
]
