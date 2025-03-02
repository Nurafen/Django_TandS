from django.urls import path
from . import views

app_name = 'adminpanel'

urlpatterns = [
    path('salesorders/<int:order_id>/update/', views.salesorder_update, name='salesorder_update'),
    path('salesorders/', views.salesorder_list, name='salesorder_list'),
    path('products/<int:product_id>/update/', views.product_update, name='product_update'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/', views.product_list, name='product_list'),
    path('users/<int:user_id>/update/', views.user_update, name='user_update'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/', views.user_list, name='user_list'),
    path('categories/<int:category_id>/update/', views.category_update, name='category_update'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/', views.category_list, name='category_list'),
    path('', views.admin_panel_index, name='index'),
]
