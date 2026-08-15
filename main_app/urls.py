from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='main_app/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', views.dashboard, name='dashboard'),
    path('rooms/', views.rooms, name='rooms'),
    path('rooms/save/', views.room_save, name='room_save'),
    path('rooms/<int:pk>/delete/', views.room_delete, name='room_delete'),
    path('rooms/bookings/save/', views.booking_save, name='booking_save'),
    path('rooms/bookings/<int:pk>/checkout/', views.booking_checkout, name='booking_checkout'),
    path('rooms/bookings/<int:pk>/delete/', views.booking_delete, name='booking_delete'),
    path('groups/', views.groups, name='groups'),
    path('groups/save/', views.group_save, name='group_save'),
    path('groups/<int:pk>/checkout/', views.group_checkout, name='group_checkout'),
    path('groups/<int:pk>/delete/', views.group_delete, name='group_delete'),
    path('purchases/', views.purchases, name='purchases'),
    path('purchases/<int:pk>/delete/', views.purchase_delete, name='purchase_delete'),
    path('reports/', views.reports, name='reports'),
]
