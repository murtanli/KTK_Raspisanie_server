
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from .views import *



from django.urls import path
from . import views

urlpatterns = [
    path('users/register/', register_user, name='register-user'),
    path('users/is_admin/', check_admin_role, name='check_admin_role'),
    path('users/download_schedule/', download_schedule, name='check_admin_role'),
    path('notifications/pending/', get_pending_notifications, name='pending_notifications'),
    path('notifications/mark_sent/', mark_notification_sent, name='mark_notification_sent'),
    path('users/get_users/', get_all_users, name='get_all_users'),
    path('schedule/get_schedule/', get_schedule, name='get_schedule'),
    path('users/get_user_info/', get_user_info, name='get_user_info')

]