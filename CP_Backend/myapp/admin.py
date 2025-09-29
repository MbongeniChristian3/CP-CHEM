# myapp/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import SalesOrder, SalesOrderItem, Product, Quotation

class SalesOrderItemInline(admin.TabularInline):
    model = SalesOrderItem
    extra = 0
    readonly_fields = ('line_total',)
    fields = (
        'product', 'quotation_item', 'quantity', 'unit_price',
        'discount_percent', 'discount_amount', 'line_total', 'delivery_date'
    )

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        
        if obj and not obj.is_editable:
            readonly_fields.extend([
                'product', 'quotation_item', 'quantity', 'unit_price',
                'discount_percent', 'discount_amount', 'delivery_date'
            ])
        
        return readonly_fields

@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'customer_name', 'quotation_link', 'status_badge',
        'payment_status_badge', 'total_amount', 'order_date', 'created_by'
    )
    list_filter = (
        'status', 'payment_status', 'order_date', 'created_at',
        'customer_name', 'created_by'
    )
    search_fields = (
        'order_number', 'customer_name', 'customer_email',
        'quotation__quotation_number', 'notes', 'customer_notes'
    )
    readonly_fields = (
        'order_number', 'subtotal', 'tax_amount', 'total_amount',
        'created_at', 'updated_at', 'confirmed_at', 'is_editable',
        'can_be_confirmed', 'items_count'
    )
    
    fieldsets = (
        ('Order Information', {
            'fields': (
                'order_number', 'quotation', 'customer_name', 'customer_email', 'customer_phone', 'customer_address', 'status', 'payment_status'
            )
        }),
        ('Dates', {
            'fields': (
                'order_date', 'expected_delivery_date', 'confirmed_at'
            )
        }),
        ('Financial Details', {
            'fields': (
                'subtotal', 'tax_rate', 'tax_amount', 'discount_amount', 'total_amount'
            )
        }),
        ('Notes', {
            'fields': ('notes', 'customer_notes', 'terms_and_conditions'),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': (
                'created_by', 'confirmed_by', 'created_at', 'updated_at',
                'is_editable', 'can_be_confirmed', 'items_count'
            ),
            'classes': ('collapse',)
        })
    )
    
    inlines = [SalesOrderItemInline]
    
    actions = ['confirm_orders', 'cancel_orders']
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        
        if obj and not obj.is_editable:
            readonly_fields.extend([
                'quotation', 'customer_name', 'customer_email', 'customer_phone', 'customer_address', 'tax_rate', 'discount_amount',
                'notes', 'customer_notes', 'terms_and_conditions'
            ])
        
        return readonly_fields
    
    def quotation_link(self, obj):
        if obj.quotation:
            url = reverse('admin:quotations_quotation_change', args=[obj.quotation.pk])
            return format_html('<a href="{}">{}</a>', url, obj.quotation.quotation_number)
        return '-'
    quotation_link.short_description = 'Quotation'
    
    def status_badge(self, obj):
        colors = {
            'draft': '#6c757d',
            'confirmed': '#007bff',
            'processing': '#ffc107',
            'shipped': '#fd7e14',
            'delivered': '#28a745',
            'cancelled': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def payment_status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'partial': '#fd7e14',
            'paid': '#28a745',
            'refunded': '#dc3545',
        }
        color = colors.get(obj.payment_status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_payment_status_display()
        )
    payment_status_badge.short_description = 'Payment Status'
    
    def confirm_orders(self, request, queryset):
        confirmed_count = 0
        for order in queryset:
            if order.confirm_order(request.user):
                confirmed_count += 1
        
        self.message_user(
            request,
            f'Successfully confirmed {confirmed_count} orders.'
        )
    confirm_orders.short_description = 'Confirm selected orders'
    
    def cancel_orders(self, request, queryset):
        cancelled_count = 0
        for order in queryset:
            if order.status not in ['delivered', 'cancelled']:
                order.status = 'cancelled'
                order.save()
                cancelled_count += 1
        
        self.message_user(
            request,
            f'Successfully cancelled {cancelled_count} orders.'
        )
    cancel_orders.short_description = 'Cancel selected orders'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SalesOrderItem)
class SalesOrderItemAdmin(admin.ModelAdmin):
    list_display = (
        'sales_order_link', 'product_link', 'quantity', 'unit_price',
        'discount_display', 'line_total', 'delivery_date'
    )
    list_filter = (
        'sales_order__status', 'product', 'delivery_date', 'created_at'
    )
    search_fields = (
        'sales_order__order_number', 'product__name', 'product__sku',
        'description'
    )
    readonly_fields = ('line_total', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Order Information', {
            'fields': ('sales_order', 'quotation_item')
        }),
        ('Product Details', {
            'fields': ('product', 'quantity', 'unit_price', 'description')
        }),
        ('Pricing', {
            'fields': ('discount_percent', 'discount_amount', 'line_total')
        }),
        ('Delivery', {
            'fields': ('delivery_date',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        
        if obj and obj.sales_order and not obj.sales_order.is_editable:
            readonly_fields.extend([
                'sales_order', 'quotation_item', 'product', 'quantity',
                'unit_price', 'discount_percent', 'discount_amount',
                'description', 'delivery_date'
            ])
        
        return readonly_fields
    
    def sales_order_link(self, obj):
        if obj.sales_order:
            url = reverse('admin:sales_orders_salesorder_change', args=[obj.sales_order.pk])
            return format_html('<a href="{}">{}</a>', url, obj.sales_order.order_number)
        return '-'
    sales_order_link.short_description = 'Sales Order'
    
    def product_link(self, obj):
        if obj.product:
            url = reverse('admin:products_product_change', args=[obj.product.pk])
            return format_html('<a href="{}">{}</a>', url, obj.product.name)
        return '-'
    product_link.short_description = 'Product'
    
    def discount_display(self, obj):
        if obj.discount_percent > 0:
            return f'{obj.discount_percent}% (${obj.discount_amount})'
        elif obj.discount_amount > 0:
            return f'${obj.discount_amount}'
        return '-'
    discount_display.short_description = 'Discount'
    
    def has_delete_permission(self, request, obj=None):
        if obj and obj.sales_order and not obj.sales_order.is_editable:
            return False
        return super().has_delete_permission(request, obj)