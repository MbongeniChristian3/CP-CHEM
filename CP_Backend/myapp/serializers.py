from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Product, Quotation, QuotationItem, MyModel
from .models import Warehouse, MyModel, Product, Quotation, QuotationItem


class MyModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyModel
        fields = '__all__'


# serializers.py
class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ['id', 'name']


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'sku',
            'stock_quantity', 'category', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# Quotation Item Serializer
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


# Quotation Serializer (Read)
class QuotationSerializer(serializers.ModelSerializer):
    items = QuotationItemSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Quotation
        fields = [
            'id', 'quotation_number', 'customer_name', 'customer_email',
            'customer_phone', 'customer_address', 'status', 'total_amount',
            'discount_percentage', 'discount_amount', 'tax_percentage',
            'tax_amount', 'final_amount', 'notes', 'valid_until',
            'created_by', 'created_by_name', 'items',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'quotation_number', 'total_amount', 'discount_amount',
            'tax_amount', 'final_amount', 'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


# Quotation Create Serializer (Write + Items)
class QuotationCreateSerializer(serializers.ModelSerializer):
    items = QuotationItemSerializer(many=True, write_only=True)

    class Meta:
        model = Quotation
        fields = [
            'customer_name', 'customer_email', 'customer_phone',
            'customer_address', 'discount_percentage', 'tax_percentage',
            'notes', 'valid_until', 'items'
        ]

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        validated_data['created_by'] = self.context['request'].user
        quotation = Quotation.objects.create(**validated_data)

        for item_data in items_data:
            QuotationItem.objects.create(quotation=quotation, **item_data)

        quotation.calculate_totals()
        return quotation


# Quotation Update Serializer
class QuotationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quotation
        fields = [
            'customer_name', 'customer_email', 'customer_phone',
            'customer_address', 'status', 'discount_percentage',
            'tax_percentage', 'notes', 'valid_until'
        ]

    def update(self, instance, validated_data):
        quotation = super().update(instance, validated_data)
        quotation.calculate_totals()
        return quotation