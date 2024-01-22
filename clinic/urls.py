from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

admin.site.site_header = "Bless and Joy Wellness Administration"
admin.site.site_title = "Bless and Joy Wellness Site Admin"
admin.site.index_title = "Welcome to the Bless and Joy Wellness Admin"

urlpatterns = [
    path('yana/', admin.site.urls),
    path('', include('website.urls')),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
]
