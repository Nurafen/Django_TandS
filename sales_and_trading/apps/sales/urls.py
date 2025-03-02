from django.urls import path
from .views import (
    SalesOrderListCreateView, SalesOrderDetailView,
    InvoiceCreateView, InvoiceRetrievePDFView
)

urlpatterns = [
    path('invoices/', InvoiceCreateView.as_view(), name='invoice_create'),
    path('invoices/<int:pk>/', InvoiceRetrievePDFView.as_view(), name='invoice_pdf'),
    path('orders/', SalesOrderListCreateView.as_view(), name='salesorder_list_create'),
    path('orders/<int:pk>/', SalesOrderDetailView.as_view(), name='salesorder_detail'),
]
