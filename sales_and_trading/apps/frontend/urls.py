from django.urls import path
from . import views

app_name = 'frontend'

urlpatterns = [
    path('sales/orders/<int:order_id>/stripe/cancel/',
         views.stripe_payment_cancel_view, name='stripe_cancel'),
    path('sales/orders/<int:order_id>/stripe/success/',
         views.stripe_payment_success_view, name='stripe_success'),
    path('sales/orders/<int:order_id>/stripe/checkout/',
         views.start_stripe_checkout_view, name='stripe_checkout'),
    path('sales/orders/<int:order_id>/invoice/',
         views.generate_invoice_frontend_view,
         name='generate_invoice_frontend'),
    path('trading/transactions/', views.list_transactions_view, name='list_transactions'),
    path('trading/transactions/create/', views.create_transaction_view, name='create_transaction'),
    path('trading/orders/<int:order_id>/', views.trading_order_detail_view, name='trading_order_detail'),
    path('trading/orders/', views.list_trading_orders_view, name='list_trading_orders'),
    path('trading/orders/create/', views.create_trading_order_view, name='create_trading_order'),
    path('products/<int:product_id>/update/', views.update_product_view, name='update_product'),
    path('products/create/', views.create_product_view, name='create_product'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('my-orders/<int:order_id>/', views.order_detail_view, name='order_detail'),
    path('my-orders/', views.my_orders_view, name='my_orders'),
    path('create-order/', views.create_order_view, name='create_order'),
    path('products/', views.product_list_view, name='product_list'),
    path('logout/', views.logout_view, name='logout'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('', views.index_view, name='index'),
]
