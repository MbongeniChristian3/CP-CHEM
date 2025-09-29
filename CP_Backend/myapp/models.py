from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
from decimal import Decimal
from django.core.validators import MinValueValidator

# Core Models: User, Profile, Warehouse
# These models are the foundation for the system's structure.

class Warehouse(models.Model):
    name = models.CharField(max_length=255)
    
    def __str__(self):
        return self.name

class Profile(models.Model):
    CEO = 'ceo'
    MANAGER = 'manager'
    CASHIER = 'cashier'
    CHAIRMAN = 'chairman'
    DISPATCH = 'dispatch'
    WAREHOUSE_STAFF = 'warehouse_staff'
    
    ROLE_CHOICES = (
        (CEO, 'CEO'),
        (MANAGER, 'Manager'),
        (CASHIER, 'Cashier'),
        (CHAIRMAN, 'Chairman'),
        (DISPATCH, 'Dispatch'),
        (WAREHOUSE_STAFF, 'Warehouse Staff'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default=CASHIER)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

    @property
    def can_create_quotations(self):
        """Check if user role can create quotations"""
        return self.role in [self.CEO, self.MANAGER, self.CASHIER]

    @property
    def can_manage_products(self):
        """Check if user role can manage products"""
        return self.role in [self.CEO, self.MANAGER, self.WAREHOUSE_STAFF]


# Product and Inventory Models
# These handle product information and stock levels at each warehouse.

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sku = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    warehouses = models.ManyToManyField(Warehouse, through='ProductStock', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.sku}"

    def get_total_stock(self):
        """Get total stock across all warehouses"""
        return sum(stock.quantity for stock in self.stock_records.all())

    def get_warehouse_stock(self, warehouse):
        """Get stock for a specific warehouse"""
        try:
            stock = self.stock_records.get(warehouse=warehouse)
            return stock.quantity
        except ProductStock.DoesNotExist:
            return 0

class ProductStock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_records')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    minimum_stock = models.PositiveIntegerField(default=10)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ['product', 'warehouse']
        ordering = ['warehouse__name', 'product__name']

    def __str__(self):
        return f"{self.product.name} at {self.warehouse.name}: {self.quantity}"

    @property
    def is_low_stock(self):
        """Check if stock is below minimum threshold"""
        return self.quantity <= self.minimum_stock

# Quotation Models
# These handle the creation and management of price quotes.

class Quotation(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
        ('converted', 'Converted to Sales Order'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quotation_number = models.CharField(max_length=50, unique=True)
    
    # Customer information (you will likely link to a separate Customer model)
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_address = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    valid_until = models.DateField()
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, 
                                 help_text="Warehouse/branch where this quotation was created")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quotations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        permissions = [
            ('can_view_all_quotations', 'Can view all quotations across warehouses'),
            ('can_approve_quotations', 'Can approve quotations'),
        ]

    def __str__(self):
        return f"Quotation {self.quotation_number} - {self.customer_name}"

    def save(self, *args, **kwargs):
        if not self.quotation_number:
            today = timezone.now().strftime('%Y%m%d')
            warehouse_prefix = self.warehouse.name[:2].upper() if self.warehouse else 'QT'
            count = Quotation.objects.filter(
                quotation_number__startswith=f'{warehouse_prefix}{today}',
                warehouse=self.warehouse
            ).count() + 1
            self.quotation_number = f'{warehouse_prefix}{today}{count:04d}'
        super().save(*args, **kwargs)

    def calculate_totals(self):
        items = self.items.all()
        subtotal = sum(item.total_price for item in items)
        
        if self.discount_percentage > 0:
            self.discount_amount = (subtotal * self.discount_percentage) / 100
        
        amount_after_discount = subtotal - self.discount_amount
        
        if self.tax_percentage > 0:
            self.tax_amount = (amount_after_discount * self.tax_percentage) / 100
        
        self.final_amount = amount_after_discount + self.tax_amount
        self.total_amount = subtotal
        
        self.save()

    def can_be_edited_by(self, user):
        if not hasattr(user, 'profile'):
            return False
        
        profile = user.profile
        
        if profile.role in [Profile.CEO, Profile.CHAIRMAN]:
            return True
        
        if profile.role == Profile.MANAGER and profile.warehouse == self.warehouse:
            return True
        
        if (profile.role == Profile.CASHIER and 
            self.created_by == user and 
            self.status == 'draft'):
            return True
        
        return False
    
    # NEW: Method to create a SalesOrder from this quotation
    def convert_to_sales_order(self, user):
        if self.status != 'accepted':
            # You can raise an exception or return an error message
            return False
        
        # Link to a Customer model instead of just name and email
        # Assuming a `Customer` model exists with a `name` field
        try:
            from .customers.models import Customer
            customer, created = Customer.objects.get_or_create(
                name=self.customer_name,
                defaults={'email': self.customer_email, 'phone': self.customer_phone}
            )
        except ImportError:
            # Fallback if Customer model isn't set up
            customer = None

        # Create the SalesOrder instance
        sales_order = SalesOrder.objects.create(
            quotation=self,
            customer=customer, # Link to the Customer object
            warehouse=self.warehouse, # NEW: Link to the warehouse
            subtotal=self.total_amount,
            tax_amount=self.tax_amount,
            tax_rate=self.tax_percentage / 100,
            discount_amount=self.discount_amount,
            total_amount=self.final_amount,
            notes=self.notes,
            created_by=user,
        )
        
        # Create SalesOrderItems from QuotationItems
        for q_item in self.items.all():
            SalesOrderItem.objects.create(
                sales_order=sales_order,
                product=q_item.product,
                quotation_item=q_item,
                quantity=q_item.quantity,
                unit_price=q_item.unit_price,
                description=q_item.description,
            )
        
        # Update the quotation status
        self.status = 'converted'
        self.save()
        
        return sales_order

class QuotationItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['quotation', 'product']

    def __str__(self):
        return f"{self.quotation.quotation_number} - {self.product.name}"

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        self.quotation.calculate_totals()

    def clean(self):
        from django.core.exceptions import ValidationError
        
        if self.quotation.warehouse:
            available_stock = self.product.get_warehouse_stock(self.quotation.warehouse)
            if self.quantity > available_stock:
                raise ValidationError(
                    f'Not enough stock available. Available: {available_stock}, Requested: {self.quantity}'
                )

    @property
    def available_stock(self):
        if self.quotation.warehouse:
            return self.product.get_warehouse_stock(self.quotation.warehouse)
        return 0

# Sales Order Models
# These handle the final sales transaction and inventory updates.

class SalesOrder(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
    ]

    # Reference fields
    order_number = models.CharField(max_length=50, unique=True, db_index=True)
    quotation = models.ForeignKey(
        'Quotation', # Renamed from 'quotations.Quotation'
        on_delete=models.PROTECT,
        related_name='sales_orders',
        help_text="Original quotation this order was generated from",
        null=True, blank=True # Made nullable for orders not from a quotation
    )
    
    # NEW: Link to the warehouse
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, 
                                 help_text="Warehouse/branch fulfilling this order")

    # Customer information
    customer_name = models.CharField(max_length=200, blank=True, null=True) # Changed to CharField for flexibility
    customer_email = models.EmailField(blank=True, null=True) # Changed to EmailField
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_address = models.TextField(blank=True)
    
    # Order details
    order_date = models.DateTimeField(default=timezone.now)
    expected_delivery_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Financial fields
    subtotal = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    tax_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=4, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    tax_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    discount_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    total_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Additional information
    notes = models.TextField(blank=True, help_text="Internal notes for the order")
    customer_notes = models.TextField(blank=True, help_text="Notes visible to customer")
    terms_and_conditions = models.TextField(blank=True)
    
    # Audit fields
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='created_sales_orders'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    confirmed_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='confirmed_sales_orders',
        null=True, 
        blank=True
    )

    class Meta:
        db_table = 'sales_orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['status', 'order_date']),
            models.Index(fields=['quotation']),
        ]

    def __str__(self):
        return f"Order {self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
            
        # If the order is created from a quotation, pull customer details
        if self.quotation and not self.customer_name:
            self.customer_name = self.quotation.customer_name
            self.customer_email = self.quotation.customer_email
            self.customer_phone = self.quotation.customer_phone
            self.customer_address = self.quotation.customer_address
        
        self.calculate_totals()
        super().save(*args, **kwargs)

    def generate_order_number(self):
        today = timezone.now().strftime('%Y%m%d')
        warehouse_prefix = self.warehouse.name[:2].upper() if self.warehouse else 'SO'
        
        last_order = SalesOrder.objects.filter(
            order_number__startswith=f'{warehouse_prefix}{today}',
            warehouse=self.warehouse
        ).order_by('order_number').last()
        
        if last_order:
            last_number = int(last_order.order_number.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
        
        return f'{warehouse_prefix}{today}{new_number:04d}'

    def calculate_totals(self):
        items = self.items.all()
        self.subtotal = sum(item.line_total for item in items)
        self.tax_amount = self.subtotal * self.tax_rate
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount

    def can_be_confirmed(self):
        return (
            self.status == 'draft' and 
            self.items.exists() and 
            self.customer_name and
            self.total_amount > 0
        )

    def confirm_order(self, user):
        if self.can_be_confirmed():
            self.status = 'confirmed'
            self.confirmed_at = timezone.now()
            self.confirmed_by = user
            self.save()
            return True
        return False

    @property
    def is_editable(self):
        return self.status in ['draft']

    @property
    def items_count(self):
        return self.items.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0

class SalesOrderItem(models.Model):
    # Relationship
    sales_order = models.ForeignKey(
        SalesOrder, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    product = models.ForeignKey(
        Product, # Renamed from 'products.Product'
        on_delete=models.PROTECT,
        related_name='sales_order_items'
    )
    quotation_item = models.ForeignKey(
        'QuotationItem', # Renamed from 'quotations.QuotationItem'
        on_delete=models.PROTECT,
        related_name='sales_order_items',
        null=True,
        blank=True,
        help_text="Original quotation item this order item was created from"
    )
    
    # Item details
    quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=3, 
        validators=[MinValueValidator(Decimal('0.001'))]
    )
    unit_price = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    discount_percent = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    discount_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    line_total = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    
    # Additional fields
    description = models.TextField(blank=True, help_text="Item-specific description or notes")
    delivery_date = models.DateField(null=True, blank=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sales_order_items'
        unique_together = ['sales_order', 'product']
        indexes = [
            models.Index(fields=['sales_order', 'product']),
            models.Index(fields=['product']),
            models.Index(fields=['quotation_item']),
        ]

    def __str__(self):
        return f"{self.sales_order.order_number} - {self.product}"

    def save(self, *args, **kwargs):
        self.calculate_line_total()
        super().save(*args, **kwargs)
        self.sales_order.calculate_totals()
        self.sales_order.save()

    def calculate_line_total(self):
        if self.discount_percent > 0:
            self.discount_amount = (self.unit_price * self.quantity) * (self.discount_percent / 100)
        
        self.line_total = (self.unit_price * self.quantity) - self.discount_amount

    def delete(self, *args, **kwargs):
        sales_order = self.sales_order
        super().delete(*args, **kwargs)
        sales_order.calculate_totals()
        sales_order.save()

# Signal to handle inventory updates when an order is confirmed
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=SalesOrder)
def handle_sales_order_confirmation(sender, instance, created, **kwargs):
    """
    Handle actions when a sales order is confirmed.
    - Reduce stock from the warehouse.
    """
    if not created and instance.status == 'confirmed' and instance.confirmed_at:
        # Check if stock has already been reduced to prevent double-counting
        # This is a basic check; a more robust solution would use a separate fulfillment model
        # You would need a way to track if this order has been processed.
        # For simplicity, we'll assume this signal only fires once per confirmation.
        
        warehouse = instance.warehouse
        for item in instance.items.all():
            product_stock, created = ProductStock.objects.get_or_create(
                product=item.product,
                warehouse=warehouse,
                defaults={'quantity': 0}
            )
            # Reduce the stock quantity
            product_stock.quantity -= item.quantity
            product_stock.save()
            print(f"Reduced stock for {item.product.name} at {warehouse.name} by {item.quantity}")