import os
import csv
from django.utils import timezone
from django.conf import settings
from celery import shared_task
from apps.trading.models import Order
from apps.sales.models import SalesOrder


def generate_report_file(file_path):
    """Создание CSV-отчета с новой структурой."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    orders_list = Order.objects.select_related('product', 'user').all()
    sales_list = SalesOrder.objects.select_related('customer').all()

    total_orders = orders_list.count()
    total_quantity = sum(o.quantity for o in orders_list)
    total_amount = sum(o.quantity * o.price for o in orders_list)

    total_sales_orders = sales_list.count()
    total_sales_sum = sum(s.total for s in sales_list)

    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        # Заголовок
        writer.writerow(["Trading & Sales Report"])
        writer.writerow(["Generated At:", timezone.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow([])

        # Раздел Orders
        writer.writerow(["=== ORDERS ==="])
        writer.writerow(["Order ID", "User", "Product", "Type", "Quantity", "Unit Price", "Total Price", "Created At"])

        for o in orders_list:
            writer.writerow([
                o.id,
                o.user.username,
                o.product.name,
                o.order_type,
                o.quantity,
                f"{o.price:.2f}",
                f"{o.quantity * o.price:.2f}",
                o.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            ])

        writer.writerow([])

        # Раздел Sales Orders
        writer.writerow(["=== SALES ORDERS ==="])
        writer.writerow(["Sales Order ID", "Customer", "Status", "Created At", "Total Amount"])

        for s in sales_list:
            writer.writerow([
                s.id,
                s.customer.username,
                s.status,
                s.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                f"{s.total:.2f}",
            ])

        writer.writerow([])

        # Аналитика
        writer.writerow(["=== ANALYTICS ==="])
        writer.writerow(["Total Orders", total_orders])
        writer.writerow(["Total Quantity (All Orders)", total_quantity])
        writer.writerow(["Total Amount (All Orders)", f"{total_amount:.2f}"])
        writer.writerow([])
        writer.writerow(["Total Sales Orders", total_sales_orders])
        writer.writerow(["Total Sales Sum", f"{total_sales_sum:.2f}"])


@shared_task
def generate_report_task():
    """Запуск фоновой задачи для генерации отчета."""
    t = timezone.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"analytics_report_{t}.csv"
    file_path = os.path.join(settings.MEDIA_ROOT, "reports", file_name)
    generate_report_file(file_path)
    return file_path


def generate_report_synchronously():
    """Генерация отчета без Celery (синхронно)."""
    t = timezone.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"analytics_report_{t}.csv"
    file_path = os.path.join(settings.MEDIA_ROOT, "reports", file_name)
    generate_report_file(file_path)
    return file_path
