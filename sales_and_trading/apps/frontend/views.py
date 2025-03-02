from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings

import stripe

from .forms import (
    RegisterForm,
    LoginForm,
    OrderForm,
    TraderProductForm,
    TradingOrderForm,
    TransactionForm
)
from apps.sales.models import SalesOrder, SalesOrderItem, Invoice, Payment
from apps.products.models import Product
from apps.trading.models import Order, Transaction
from apps.trading.utils import attempt_to_match_order
from apps.analytics.tasks import generate_report_synchronously
from sales_and_trading.utils.pdf_generation import render_pdf, pdf_response


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            if user:
                login(request, user)
                messages.success(request, f"Welcome, {user.username}!")
                return redirect('frontend:index')
    else:
        form = LoginForm()
    return render(request, 'frontend/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('frontend:index')


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Registration successful. Please log in.")
            return redirect('frontend:login')
    else:
        form = RegisterForm()
    return render(request, 'frontend/register.html', {'form': form})


def index_view(request):
    return render(request, 'frontend/index.html')


@login_required
def analytics_view(request):
    if not (request.user.role == 'admin' or request.user.is_staff):
        return HttpResponseForbidden("You do not have permission to access analytics.")
    if request.method == 'POST':
        file_path = generate_report_synchronously()
        with open(file_path, 'rb') as f:
            file_data = f.read()
        response = HttpResponse(file_data, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="analytics_report.csv"'
        return response
    return render(request, 'frontend/analytics.html')


@login_required
def product_list_view(request):
    products = cache.get('cached_product_list')
    if products is None:
        products = list(Product.objects.select_related('category').all())
        cache.set('cached_product_list', products, timeout=60)
    return render(request, 'frontend/product_list.html', {'products': products})


@login_required
def create_product_view(request):
    if not (request.user.role == 'admin' or request.user.role == 'trader' or request.user.is_staff):
        return HttpResponseForbidden("You do not have permission to create products.")
    if request.method == 'POST':
        form = TraderProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            cache.delete('cached_product_list')
            messages.success(request, "Product created successfully.")
            return redirect('frontend:product_list')
    else:
        form = TraderProductForm()
    return render(request, 'frontend/create_product.html', {'form': form})


@login_required
def update_product_view(request, product_id):
    if not (request.user.role == 'admin' or request.user.role == 'trader' or request.user.is_staff):
        return HttpResponseForbidden("You do not have permission to edit products.")
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = TraderProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated successfully.")
            return redirect('frontend:product_list')
    else:
        form = TraderProductForm(instance=product)
    return render(request, 'frontend/update_product.html', {'form': form, 'product': product})


@login_required
def create_order_view(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            product = form.cleaned_data['product']
            quantity = form.cleaned_data['quantity']
            price = form.cleaned_data['price']
            order = SalesOrder.objects.create(customer=request.user, status='pending', discount_percent=0)
            SalesOrderItem.objects.create(
                sales_order=order, product=product,
                quantity=quantity, price=price
            )
            messages.success(request, f"Order #{order.id} created successfully.")
            return redirect('frontend:my_orders')
    else:
        form = OrderForm()
    return render(request, 'frontend/create_order.html', {'form': form})


@login_required
def my_orders_view(request):
    orders = SalesOrder.objects.filter(customer=request.user).order_by('-created_at')
    return render(request, 'frontend/order_list.html', {'orders': orders})


@login_required
def order_detail_view(request, order_id):
    order = get_object_or_404(SalesOrder, id=order_id, customer=request.user)
    return render(request, 'frontend/order_detail.html', {'order': order})


@login_required
def create_trading_order_view(request):
    if request.method == 'POST':
        form = TradingOrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()
            attempt_to_match_order(order)
            messages.success(request, f"{order.order_type.capitalize()} order #{order.id} placed successfully.")
            return redirect('frontend:list_trading_orders')
    else:
        form = TradingOrderForm()
    return render(request, 'frontend/create_trading_order.html', {'form': form})


@login_required
def list_trading_orders_view(request):
    if request.user.role in ['admin', 'trader']:
        orders = Order.objects.select_related('product').all().order_by('-created_at')
    else:
        orders = Order.objects.select_related('product').filter(user=request.user).order_by('-created_at')
    return render(request, 'frontend/list_trading_orders.html', {'orders': orders})


@login_required
def trading_order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.user != request.user and request.user.role not in ['admin', 'trader']:
        return HttpResponseForbidden("You don't have permission to view this order.")
    return render(request, 'frontend/trading_order_detail.html', {'order': order})


@login_required
def create_transaction_view(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save()
            messages.success(request, f"Transaction #{transaction.id} created for Order #{transaction.order.id}.")
            return redirect('frontend:list_transactions')
    else:
        form = TransactionForm()
    return render(request, 'frontend/create_transaction.html', {'form': form})


@login_required
def list_transactions_view(request):
    if request.user.role in ['admin', 'trader']:
        transactions = Transaction.objects.select_related('order').all().order_by('-executed_at')
    else:
        transactions = Transaction.objects.select_related('order').filter(order__user=request.user).order_by('-executed_at')
    return render(request, 'frontend/list_transactions.html', {'transactions': transactions})


@login_required
def generate_invoice_frontend_view(request, order_id):
    sales_order = get_object_or_404(SalesOrder, id=order_id)
    user_role = request.user.role if hasattr(request.user, 'role') else 'customer'

    if request.user != sales_order.customer and user_role not in ['admin', 'sales']:
        return HttpResponseForbidden("You do not have permission to generate an invoice for this order.")

    invoice, _ = Invoice.objects.get_or_create(sales_order=sales_order)

    context = {
        'invoice': invoice,
        'date': timezone.now(),
    }

    pdf_content = render_pdf('frontend/invoice.html', context_dict=context)
    filename = f"invoice_{invoice.id}.pdf"
    return pdf_response(pdf_content, filename=filename)


@login_required
def start_stripe_checkout_view(request, order_id):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    sales_order = get_object_or_404(SalesOrder, id=order_id)
    if request.user != sales_order.customer and request.user.role not in ['admin', 'sales']:
        return HttpResponseForbidden("You do not have permission for this order.")

    if sales_order.status == 'paid':
        messages.info(request, "Order is already paid.")
        return redirect('frontend:order_detail', order_id=order_id)

    amount_cents = int(sales_order.total * 100)

    # Create or update payment record
    payment, _ = Payment.objects.get_or_create(sales_order=sales_order)
    payment.amount = sales_order.total
    payment.save()

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': f"SalesOrder #{sales_order.id}"},
                    'unit_amount': amount_cents,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri(f"/sales/orders/{order_id}/stripe/success/"),
            cancel_url=request.build_absolute_uri(f"/sales/orders/{order_id}/stripe/cancel/"),
        )
    except stripe.error.AuthenticationError:
        messages.error(request, "Stripe authentication failed. Please check your API key.")
        return redirect('frontend:order_detail', order_id=order_id)

    payment.stripe_session_id = session.id
    payment.save()

    return redirect(session.url)


@login_required
def stripe_payment_success_view(request, order_id):
    sales_order = get_object_or_404(SalesOrder, id=order_id)
    payment = getattr(sales_order, 'payment', None)
    if payment is None:
        messages.error(request, "No payment record found.")
        return redirect('frontend:order_detail', order_id=order_id)
    payment.status = 'successful'
    payment.save()
    sales_order.status = 'completed'
    sales_order.save()
    messages.success(request, "Payment successful! The order is now completed.")
    return redirect('frontend:order_detail', order_id=sales_order.id)


@login_required
def stripe_payment_cancel_view(request, order_id):
    sales_order = get_object_or_404(SalesOrder, id=order_id)
    payment = getattr(sales_order, 'payment', None)
    if payment:
        payment.status = 'failed'
        payment.save()
    messages.info(request, "Payment cancelled. You can try again.")
    return redirect('frontend:order_detail', order_id=order_id)
