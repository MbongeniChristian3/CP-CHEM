from rest_framework import serializers
from django.contrib.auth.models import User
from decimal import Decimal
from django.db import transaction
from .models import (
    Warehouse,
    Product, 
    ProductStock,
    Quotation, 
    QuotationItem, 
    SalesOrder, 
    SalesOrderItem,
)

# Core Serializers

class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ['id', 'name']


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'sku',
            'category', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

# Quotation Serializers (No changes needed)

class QuotationItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)

    class Meta:
        model = QuotationItem
        fields = [
            'id', 'product', 'product_name', 'product_sku',
            'quantity', 'unit_price', 'total_price', 'description',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total_price', 'created_at', 'updated_at']

    def validate(self, attrs):
        quotation_warehouse = self.context.get('quotation_warehouse')
        product = attrs.get('product')
        quantity = attrs.get('quantity')
        
        # Ensure quantity is not zero or negative
        if quantity is not None and quantity <= 0:
            raise serializers.ValidationError({"quantity": "Quantity must be greater than 0."})

        if quotation_warehouse and product and quantity is not None:
            # You must ensure Product has a get_warehouse_stock method
            available_stock = product.get_warehouse_stock(quotation_warehouse)
            if quantity > available_stock:
                raise serializers.ValidationError(
                    f"Not enough stock for '{product.name}'. Available: {available_stock}, Requested: {quantity}"
                )
        return attrs


class QuotationSerializer(serializers.ModelSerializer):
    items = QuotationItemSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)

    class Meta:
        model = Quotation
        fields = [
            'id', 'quotation_number', 'customer_name', 'customer_email',
            'customer_phone', 'customer_address', 'status', 'total_amount',
            'discount_percentage', 'discount_amount', 'tax_percentage',
            'tax_amount', 'final_amount', 'notes', 'valid_until',
            'warehouse', 'warehouse_name', 'created_by', 'created_by_name', 
            'items', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'quotation_number', 'total_amount', 'discount_amount',
            'tax_amount', 'final_amount', 'created_at', 'updated_at',
            'created_by' # Ensure created_by is read_only if set in view/create method
        ]
        
    def create(self, validated_data):
        # Setting created_by here is redundant if done in the ViewSet's perform_create, 
        # but is safe if the view doesn't handle it.
        if 'request' in self.context and self.context['request'].user.is_authenticated:
            validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

# Sales Order Serializers

class SalesOrderItemSerializer(serializers.ModelSerializer):
    # Added source for consistency. line_total is typically calculated on the model.
    line_total = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True, source='get_line_total')
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)

    class Meta:
        model = SalesOrderItem
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'quotation_item',
            'quantity', 'unit_price', 'discount_percent', 'discount_amount',
            'line_total', 'description', 'delivery_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'line_total', 'created_at', 'updated_at']
        
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        return value

    def validate_unit_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Unit price cannot be negative.")
        return value

    def validate_discount_percent(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Discount percent must be between 0 and 100.")
        return value


class SalesOrderCreateUpdateSerializer(serializers.ModelSerializer):
    # --- FIX 1: Make items WRITE-ONLY. This prevents DRF from trying to create 
    # nested objects automatically during the initial save, letting us handle it manually.
    items = SalesOrderItemSerializer(many=True, required=False, write_only=True)
    
    class Meta:
        model = SalesOrder
        fields = [
            'id', 'warehouse', 'customer_name', 'customer_email', 'customer_phone', 'customer_address',
            'expected_delivery_date', 'tax_rate', 'discount_amount', 'notes', 
            'customer_notes', 'terms_and_conditions', 'items'
        ]
        # Ensure 'id' is here for updates
        read_only_fields = ['id'] 
        
    def create(self, validated_data):
        # --- FIX 2: Manually validate and create nested items ---
        items_data = validated_data.pop('items', [])
        
        with transaction.atomic():
            # NOTE: Your ViewSet's perform_create handles 'created_by' and 'warehouse' 
            # if they aren't provided in the request body. 
            # If the ViewSet sets them, they should NOT be set here.
            
            # Create the parent Sales Order
            sales_order = SalesOrder.objects.create(**validated_data)
            
            # Create nested items, validating them against the SalesOrderItemSerializer
            for item_data in items_data:
                # We need to explicitly validate the item data here
                item_serializer = SalesOrderItemSerializer(data=item_data)
                
                # This is the point where the 400 error is caught if item data is bad
                item_serializer.is_valid(raise_exception=True) 
                
                # Save the item, linking it to the newly created sales_order
                item_serializer.save(sales_order=sales_order)
            
            # Trigger the final save on the SalesOrder to recalculate totals
            sales_order.save() 
        
        return sales_order

    def update(self, instance, validated_data):
        # NOTE: If you pass 'items' data to update, you need logic to manage item
        # updates (e.g., matching by ID, deleting missing items, creating new ones). 
        # Since 'items' is write_only=True, it is excluded from super().update.
        
        if not instance.is_editable:
            raise serializers.ValidationError(
                f"Cannot modify sales order in '{instance.status}' status"
            )
        
        # Handle update of parent fields
        instance = super().update(instance, validated_data)
        
        # Recalculate totals and save
        instance.save() 
        return instance
    

class SalesOrderDetailSerializer(serializers.ModelSerializer):
    # ... (rest of the serializer remains the same)
    items = SalesOrderItemSerializer(many=True, read_only=True)
    items_count = serializers.ReadOnlyField()
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    confirmed_by_name = serializers.CharField(source='confirmed_by.username', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    is_editable = serializers.ReadOnlyField()
    can_be_confirmed = serializers.ReadOnlyField()
    
    class Meta:
        model = SalesOrder
        fields = [
            'id', 'order_number', 'quotation', 'warehouse', 'warehouse_name',
            'customer_name', 'customer_email', 'customer_phone', 'customer_address',
            'order_date', 'expected_delivery_date', 'status', 'payment_status',
            'subtotal', 'tax_rate', 'tax_amount', 'discount_amount', 'total_amount',
            'notes', 'customer_notes', 'terms_and_conditions',
            'items', 'items_count', 'is_editable', 'can_be_confirmed',
            'created_by', 'created_by_name', 'created_at', 'updated_at',
            'confirmed_at', 'confirmed_by', 'confirmed_by_name'
        ]

# Specialized Serializers for Actions (No changes needed)
# ... (rest of the file is unchanged)