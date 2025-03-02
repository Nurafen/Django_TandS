from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

from django.contrib.auth import get_user_model
User = get_user_model()

from .models import SalesOrder, SalesOrderItem, Invoice
from .serializers import SalesOrderSerializer, InvoiceSerializer
from sales_and_trading.utils.pdf_generation import render_pdf, pdf_response

class InvoiceRetrievePDFView(generics.RetrieveAPIView):
    """
    Retrieve an existing invoice and return as a PDF download.
    """
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        invoice = self.get_object()
        sales_order = invoice.sales_order
        context = {
            'invoice': invoice,
            'sales_order': sales_order,
            'items': sales_order.items.all(),
            'customer': sales_order.customer,
            'total': sales_order.total,
            'date': timezone.now(),
        }
        pdf_content = render_pdf('invoice.html', context_dict=context)
        return pdf_response(pdf_content, filename=f"invoice_{invoice.id}.pdf")

class InvoiceCreateView(generics.CreateAPIView):
    """
    Create an invoice for a given SalesOrder.
    Only Admin or Sales can generate an invoice once order is approved.
    """
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        order_id = self.request.data.get('sales_order')
        sales_order = get_object_or_404(SalesOrder, id=order_id)
        if user.role not in ['admin', 'sales']:
            raise permissions.PermissionDenied("You do not have permission to create invoices.")
        if sales_order.status != 'approved':
            raise ValueError("Cannot generate invoice for non-approved order.")
        if hasattr(sales_order, 'invoice'):
            raise ValueError("Invoice already exists for this order.")
        serializer.save(sales_order=sales_order)

class SalesOrderListCreateView(generics.ListCreateAPIView):
    """
    GET: List all Sales Orders (Admins & Sales can see all, customers see only theirs).
    POST: Create a new Sales Order (Customers can create for themselves).
    """
    queryset = SalesOrder.objects.all()
    serializer_class = SalesOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin', 'sales']:
            return SalesOrder.objects.all()
        return SalesOrder.objects.filter(customer=user)

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['customer'] = request.user.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class SalesOrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a Sales Order.
    PUT/PATCH: Update the order (e.g., admin/sales can approve).
    DELETE: Cancel or delete the order (admin/sales).
    """
    queryset = SalesOrder.objects.all()
    serializer_class = SalesOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin', 'sales']:
            return SalesOrder.objects.all()
        return SalesOrder.objects.filter(customer=user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        user = request.user
        data = request.data.copy()
        if user.role not in ['admin', 'sales'] and 'status' in data:
            if data['status'] in ['approved', 'completed']:
                return Response({"detail": "Not allowed to approve/complete orders."},
                                status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)
