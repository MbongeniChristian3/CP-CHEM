import django_filters
from django.db import models
from .models import SalesOrder, SalesOrderItem


class SalesOrderFilter(django_filters.FilterSet):
    """
    Filter for sales orders with comprehensive filtering options
    """
    # Date filters
    order_date = django_filters.DateFilter()
    order_date_from = django_filters.DateFilter(field_name='order_date', lookup_expr='gte')
    order_date_to = django_filters.DateFilter(field_name='order_date', lookup_expr='lte')
    order_date_range = django_filters.DateFromToRangeFilter(field_name='order_date')
    
    expected_delivery_date = django_filters.DateFilter()
    expected_delivery_from = django_filters.DateFilter(
        field_name='expected_delivery_date', 
        lookup_expr='gte'
    )
    expected_delivery_to = django_filters.DateFilter(
        field_name='expected_delivery_date', 
        lookup_expr='lte'
    )
    
    created_at = django_filters.DateTimeFilter()
    created_from = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_to = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    created_date_range = django_filters.DateFromToRangeFilter(field_name='created_at')
    
    # Status filters
    status = django_filters.ChoiceFilter(choices=SalesOrder.STATUS_CHOICES)
    status_in = django_filters.MultipleChoiceFilter(
        field_name='status', 
        choices=SalesOrder.STATUS_CHOICES
    )
    payment_status = django_filters.ChoiceFilter(choices=SalesOrder.PAYMENT_STATUS_CHOICES)
    payment_status_in = django_filters.MultipleChoiceFilter(
        field_name='payment_status',
        choices=SalesOrder.PAYMENT_STATUS_CHOICES
    )
    
    # Customer filters
    customer = django_filters.NumberFilter()
    customer_name = django_filters.CharFilter(
        field_name='customer__name', 
        lookup_expr='icontains'
    )
    customer_email = django_filters.CharFilter(
        field_name='customer__email', 
        lookup_expr='icontains'
    )
    
    # Quotation filters
    quotation = django_filters.NumberFilter()
    quotation_number = django_filters.CharFilter(
        field_name='quotation__quotation_number',
        lookup_expr='icontains'
    )
    
    # Financial filters
    total_amount = django_filters.NumberFilter()
    total_amount_min = django_filters.NumberFilter(
        field_name='total_amount', 
        lookup_expr='gte'
    )
    total_amount_max = django_filters.NumberFilter(
        field_name='total_amount', 
        lookup_expr='lte'
    )
    total_amount_range = django_filters.RangeFilter(field_name='total_amount')
    
    subtotal_min = django_filters.NumberFilter(field_name='subtotal', lookup_expr='gte')
    subtotal_max = django_filters.NumberFilter(field_name='subtotal', lookup_expr='lte')
    
    # User filters
    created_by = django_filters.NumberFilter()
    created_by_username = django_filters.CharFilter(
        field_name='created_by__username',
        lookup_expr='icontains'
    )
    confirmed_by = django_filters.NumberFilter()
    
    # Text search
    search = django_filters.CharFilter(method='filter_search')
    
    # Boolean filters
    is_confirmed = django_filters.BooleanFilter(method='filter_is_confirmed')
    is_editable = django_filters.BooleanFilter(method='filter_is_editable')
    has_items = django_filters.BooleanFilter(method='filter_has_items')
    
    # Product filters (items contain specific products)
    has_product = django_filters.NumberFilter(method='filter_has_product')
    has_product_sku = django_filters.CharFilter(method='filter_has_product_sku')
    
    class Meta:
        model = SalesOrder
        fields = {
            'order_number': ['exact', 'icontains'],
            'notes': ['icontains'],
            'customer_notes': ['icontains'],
        }

    def filter_search(self, queryset, name, value):
        """
        Custom search across multiple fields
        """
        if not value:
            return queryset
            
        return queryset.filter(
            models.Q(order_number__icontains=value) |
            models.Q(customer__name__icontains=value) |
            models.Q(customer__email__icontains=value) |
            models.Q(quotation__quotation_number__icontains=value) |
            models.Q(notes__icontains=value) |
            models.Q(customer_notes__icontains=value)
        )

    def filter_is_confirmed(self, queryset, name, value):
        """Filter by confirmation status"""
        if value is True:
            return queryset.filter(confirmed_at__isnull=False)
        elif value is False:
            return queryset.filter(confirmed_at__isnull=True)
        return queryset

    def filter_is_editable(self, queryset, name, value):
        """Filter by editable status"""
        if value is True:
            return queryset.filter(status__in=['draft'])
        elif value is False:
            return queryset.exclude(status__in=['draft'])
        return queryset

    def filter_has_items(self, queryset, name, value):
        """Filter orders that have items"""
        if value is True:
            return queryset.filter(items__isnull=False).distinct()
        elif value is False:
            return queryset.filter(items__isnull=True)
        return queryset

    def filter_has_product(self, queryset, name, value):
        """Filter orders containing specific product"""
        if value:
            return queryset.filter(items__product_id=value).distinct()
        return queryset

    def filter_has_product_sku(self, queryset, name, value):
        """Filter orders containing product with specific SKU"""
        if value:
            return queryset.filter(items__product__sku__icontains=value).distinct()
        return queryset


class SalesOrderItemFilter(django_filters.FilterSet):
    """
    Filter for sales order items
    """
    # Order filters
    sales_order = django_filters.NumberFilter()
    order_number = django_filters.CharFilter(
        field_name='sales_order__order_number',
        lookup_expr='icontains'
    )
    order_status = django_filters.ChoiceFilter(
        field_name='sales_order__status',
        choices=SalesOrder.STATUS_CHOICES
    )
    
    # Product filters
    product = django_filters.NumberFilter()
    product_name = django_filters.CharFilter(
        field_name='product__name',
        lookup_expr='icontains'
    )
    product_sku = django_filters.CharFilter(
        field_name='product__sku',
        lookup_expr='icontains'
    )
    
    # Quotation filters
    quotation_item = django_filters.NumberFilter()
    from_quotation = django_filters.BooleanFilter(method='filter_from_quotation')
    
    # Quantity filters
    quantity = django_filters.NumberFilter()
    quantity_min = django_filters.NumberFilter(field_name='quantity', lookup_expr='gte')
    quantity_max = django_filters.NumberFilter(field_name='quantity', lookup_expr='lte')
    quantity_range = django_filters.RangeFilter(field_name='quantity')
    
    # Price filters
    unit_price = django_filters.NumberFilter()
    unit_price_min = django_filters.NumberFilter(field_name='unit_price', lookup_expr='gte')
    unit_price_max = django_filters.NumberFilter(field_name='unit_price', lookup_expr='lte')
    unit_price_range = django_filters.RangeFilter(field_name='unit_price')
    
    line_total_min = django_filters.NumberFilter(field_name='line_total', lookup_expr='gte')
    line_total_max = django_filters.NumberFilter(field_name='line_total', lookup_expr='lte')
    line_total_range = django_filters.RangeFilter(field_name='line_total')
    
    # Discount filters
    has_discount = django_filters.BooleanFilter(method='filter_has_discount')
    discount_percent_min = django_filters.NumberFilter(
        field_name='discount_percent', 
        lookup_expr='gte'
    )
    discount_percent_max = django_filters.NumberFilter(
        field_name='discount_percent', 
        lookup_expr='lte'
    )
    
    # Date filters
    delivery_date = django_filters.DateFilter()
    delivery_date_from = django_filters.DateFilter(
        field_name='delivery_date', 
        lookup_expr='gte'
    )
    delivery_date_to = django_filters.DateFilter(
        field_name='delivery_date', 
        lookup_expr='lte'
    )
    
    created_from = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_to = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    # Customer filters
    customer = django_filters.NumberFilter(field_name='sales_order__customer')
    customer_name = django_filters.CharFilter(
        field_name='sales_order__customer__name',
        lookup_expr='icontains'
    )
    
    class Meta:
        model = SalesOrderItem
        fields = {
            'description': ['icontains'],
        }

    def filter_from_quotation(self, queryset, name, value):
        """Filter items that originated from quotations"""
        if value is True:
            return queryset.filter(quotation_item__isnull=False)
        elif value is False:
            return queryset.filter(quotation_item__isnull=True)
        return queryset

    def filter_has_discount(self, queryset, name, value):
        """Filter items with discounts"""
        if value is True:
            return queryset.filter(
                models.Q(discount_percent__gt=0) | 
                models.Q(discount_amount__gt=0)
            )
        elif value is False:
            return queryset.filter(
                discount_percent=0, 
                discount_amount=0
            )
        return queryset


class SalesOrderDateRangeFilter(django_filters.FilterSet):
    """
    Specialized filter for date-based reporting
    """
    # Common date ranges
    today = django_filters.BooleanFilter(method='filter_today')
    this_week = django_filters.BooleanFilter(method='filter_this_week')
    this_month = django_filters.BooleanFilter(method='filter_this_month')
    this_quarter = django_filters.BooleanFilter(method='filter_this_quarter')
    this_year = django_filters.BooleanFilter(method='filter_this_year')
    
    last_7_days = django_filters.BooleanFilter(method='filter_last_7_days')
    last_30_days = django_filters.BooleanFilter(method='filter_last_30_days')
    last_90_days = django_filters.BooleanFilter(method='filter_last_90_days')
    
    class Meta:
        model = SalesOrder
        fields = []

    def filter_today(self, queryset, name, value):
        if value:
            from django.utils import timezone
            today = timezone.now().date()
            return queryset.filter(order_date__date=today)
        return queryset

    def filter_this_week(self, queryset, name, value):
        if value:
            from django.utils import timezone
            now = timezone.now()
            week_start = now.date() - timezone.timedelta(days=now.weekday())
            return queryset.filter(order_date__date__gte=week_start)
        return queryset

    def filter_this_month(self, queryset, name, value):
        if value:
            from django.utils import timezone
            now = timezone.now()
            month_start = now.replace(day=1).date()
            return queryset.filter(order_date__date__gte=month_start)
        return queryset

    def filter_this_quarter(self, queryset, name, value):
        if value:
            from django.utils import timezone
            now = timezone.now()
            quarter = (now.month - 1) // 3 + 1
            quarter_start = now.replace(month=(quarter - 1) * 3 + 1, day=1).date()
            return queryset.filter(order_date__date__gte=quarter_start)
        return queryset

    def filter_this_year(self, queryset, name, value):
        if value:
            from django.utils import timezone
            now = timezone.now()
            year_start = now.replace(month=1, day=1).date()
            return queryset.filter(order_date__date__gte=year_start)
        return queryset

    def filter_last_7_days(self, queryset, name, value):
        if value:
            from django.utils import timezone
            week_ago = timezone.now().date() - timezone.timedelta(days=7)
            return queryset.filter(order_date__date__gte=week_ago)
        return queryset

    def filter_last_30_days(self, queryset, name, value):
        if value:
            from django.utils import timezone
            month_ago = timezone.now().date() - timezone.timedelta(days=30)
            return queryset.filter(order_date__date__gte=month_ago)
        return queryset

    def filter_last_90_days(self, queryset, name, value):
        if value:
            from django.utils import timezone
            quarter_ago = timezone.now().date() - timezone.timedelta(days=90)
            return queryset.filter(order_date__date__gte=quarter_ago)
        return queryset