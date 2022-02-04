from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login', views.login_page, name='login'),
    path('logout', views.logout_page, name='logout'),
    path('register', views.register, name='register'),
    path('managerRegister', views.manager_register, name='managerRegister'),
    path('managerHome', views.manager_home, name='managerHome'),
    path('userHome', views.user_home, name='userHome'),
    path('userScheduled', views.user_scheduled, name='userScheduled'),
    path('changeCarModel', views.change_car_model, name='changeCarModel'),

    path('reset_password/', auth_views.PasswordResetView.as_view(
        template_name="password_reset.html"), name="reset_password"),
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(
        template_name="password_reset_sent.html"), name="password_reset_done"),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name="password_reset_form.html"),
         name="password_reset_confirm"),
    path('reset_password_complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name="password_reset_done.html"),
         name="password_reset_complete"),

    path('changePassword/', auth_views.PasswordChangeView.as_view(
        template_name="changePassword.html"), name="changePassword"),
    path('password_change_done/', auth_views.PasswordChangeDoneView.as_view(
        template_name="password_change_done.html"),
         name="password_change_done"),
    path('changePassword2/', auth_views.PasswordChangeView.as_view(
        template_name="changePassword2.html"), name="changePassword2"),
    path('password_change_done2/', auth_views.PasswordChangeDoneView.as_view(
        template_name="password_change_done2.html"),
         name="password_change_done2"),

]
