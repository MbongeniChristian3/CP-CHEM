# models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

# This is the new model for your warehouses or branches.
class Warehouse(models.Model):
    name = models.CharField(max_length=255)
    
    def __str__(self):
        return self.name

class MyModel(models.Model):
    # Your existing model fields
    name = models.CharField(max_length=255)
    description = models.TextField(default='')
    
    # New: Link this model to a warehouse.
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    
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
    
    # New: Link a user's profile to a specific warehouse.
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

# Product model with warehouse tracking
class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sku = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Warehouse relationship - products can be in multiple warehouses
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

# Product stock per warehouse
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

# Quotation model with warehouse context
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
    
    # Customer information
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_address = models.TextField(blank=True)
    
    # Quotation details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    notes = models.TextField(blank=True)
    valid_until = models.DateField()
    
    # Warehouse and user context
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, 
                                help_text="Warehouse/branch where this quotation was created")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quotations')
    
    # Timestamps
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
            # Generate quotation number with warehouse prefix
            today = timezone.now().strftime('%Y%m%d')
            warehouse_prefix = self.warehouse.name[:2].upper() if self.warehouse else 'QT'
            count = Quotation.objects.filter(
                quotation_number__startswith=f'{warehouse_prefix}{today}',
                warehouse=self.warehouse
            ).count() + 1
            self.quotation_number = f'{warehouse_prefix}{today}{count:04d}'
        super().save(*args, **kwargs)

    def calculate_totals(self):
        """Calculate all totals based on quotation items"""
        items = self.items.all()
        subtotal = sum(item.total_price for item in items)
        
        # Calculate discount
        if self.discount_percentage > 0:
            self.discount_amount = (subtotal * self.discount_percentage) / 100
        
        # Amount after discount
        amount_after_discount = subtotal - self.discount_amount
        
        # Calculate tax
        if self.tax_percentage > 0:
            self.tax_amount = (amount_after_discount * self.tax_percentage) / 100
        
        # Final amount
        self.final_amount = amount_after_discount + self.tax_amount
        self.total_amount = subtotal
        
        self.save()

    def can_be_edited_by(self, user):
        """Check if user can edit this quotation"""
        if not hasattr(user, 'profile'):
            return False
        
        profile = user.profile
        
        # CEO and Chairman can edit all quotations
        if profile.role in [Profile.CEO, Profile.CHAIRMAN]:
            return True
        
        # Managers can edit quotations in their warehouse
        if profile.role == Profile.MANAGER and profile.warehouse == self.warehouse:
            return True
        
        # Cashiers can only edit their own draft quotations
        if (profile.role == Profile.CASHIER and 
            self.created_by == user and 
            self.status == 'draft'):
            return True
        
        return False

# Quotation items with warehouse stock validation
class QuotationItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)  # Custom description for this item
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['quotation', 'product']

    def __str__(self):
        return f"{self.quotation.quotation_number} - {self.product.name}"

    def save(self, *args, **kwargs):
        # Calculate total price
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        
        # Update quotation totals
        self.quotation.calculate_totals()

    def clean(self):
        """Validate that there's enough stock in the warehouse"""
        from django.core.exceptions import ValidationError
        
        if self.quotation.warehouse:
            available_stock = self.product.get_warehouse_stock(self.quotation.warehouse)
            if self.quantity > available_stock:
                raise ValidationError(
                    f'Not enough stock available. Available: {available_stock}, Requested: {self.quantity}'
                )

    @property
    def available_stock(self):
        """Get available stock for this product in the quotation's warehouse"""
        if self.quotation.warehouse:
            return self.product.get_warehouse_stock(self.quotation.warehouse)
        return 0