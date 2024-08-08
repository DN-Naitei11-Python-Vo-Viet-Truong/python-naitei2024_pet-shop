from django.urls import path, include
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('shop/', views.ShopView, name='shop'),
    path('sign-in/', views.login_view, name="sign-in"),
    path('', include('django.contrib.auth.urls')),
]
