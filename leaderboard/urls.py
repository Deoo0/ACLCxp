from atexit import register
from django.urls import path
from . import views


urlpatterns = [
    path('login/', views.login, name='login'),
    path('', views.landing_page, name='home'),
    path('about/',views.about, name='about'),
    path('register/',views.register, name='register')
]