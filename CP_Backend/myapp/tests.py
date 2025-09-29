from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from django.utils import timezone
from .models import SalesOrder, SalesOrderItem


class SalesOrderModelTest(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Mock related objects (adjust according to your actual models)
        self.customer = self.create_mock_customer()
        self.quotation = self.create_mock_quotation()
        self.product = self.create_mock_product()

    def create_mock_customer(self):
        # Mock customer - adjust according to your Customer model
        from unittest.mock import Mock
        customer = Mock()
        customer.id = 1
        customer.name = 'Test Customer'
        customer.email = 'customer@test.com'
        return customer

    def create_mock_quotation(self):
        # Mock quotation - adjust according to your Quotation model
        from unittest.mock import Mock
        quotation = Mock()
        quotation.id = 1
        quotation.quotation_number = 'QUO-2025-000001'
        quotation.customer = self.customer
        quotation.status = 'approved'
        return quotation

    def create_mock_product(self):
        # Mock product - adjust according to your Product model
        from unittest.mock import Mock
        product = Mock()
        product.id = 1
        product.name = 'Test Product'
        product.sku = 'TEST-001'
        return product

    def test_order_number_generation(self):
        """Test that order numbers are generated correctly"""
        sales_order = SalesOrder(
            customer=self.customer,
            quotation=self.quotation,
            created_by=self.user
        )
        
        # Test order number generation
        order_number = sales_order.generate_order_number()
        self.assertTrue(order_number.startswith('SO-2025-'))
        self.assertTrue(len(order_number.split('-')[-1]) == 6)

    def test_sales_order_creation(self):
        """Test creating a sales order"""
        sales_order = SalesOrder.objects.create(
            customer=self.customer,
            quotation=self.quotation,
            created_by=self.user,
            tax_rate=Decimal('0.15')
        )
        
        self.assertIsNotNone(sales_order.order_number)
        self.assertEqual(sales_order.status, 'draft')
        self.assertEqual(sales_order.payment_status, 'pending')
        self.assertEqual(sales_order.tax_rate, Decimal('0.15'))

    def test_order_confirmation(self):
        """Test order confirmation process"""
        sales_order = SalesOrder.objects.create(
            customer=self.customer,
            quotation=self.quotation,
            created_by=self.user
        )
        
        # Add an item to make it confirmable
        SalesOrderItem.objects.create(
            sales_order=sales_order,
            product=self.product,
            quantity=Decimal('2'),
            unit_price=Decimal('25.00')
        )
        
        # Test confirmation
        self.assertTrue(sales_order.can_be_confirmed())
        success = sales_order.confirm_order(self.user)
        self.assertTrue(success)
        self.assertEqual(sales_order.status, 'confirmed')
        self.assertIsNotNone(sales_order.confirmed_at)
        self.assertEqual(sales_order.confirmed_by, self.user)

    def test_total_calculation(self):
        """Test automatic total calculation"""
        sales_order = SalesOrder.objects.create(
            customer=self.customer,
            quotation=self.quotation,
            created_by=self.user,
            tax_rate=Decimal('0.10'),
            discount_amount=Decimal('5.00')
        )
        
        # Add items
        item1 = SalesOrderItem.objects.create(
            sales_order=sales_order,
            product=self.product,
            quantity=Decimal('2'),
            unit_price=Decimal('25.00')
        )
        
        item2 = SalesOrderItem.objects.create(
            sales_order=sales_order,
            product=self.product,
            quantity=Decimal('1'),
            unit_price=Decimal('30.00')
        )
        
        sales_order.refresh_from_db()
        
        expected_subtotal = Decimal('80.00')  # (2 * 25) + (1 * 30)
        expected_tax = Decimal('8.00')        # 80 * 0.10
        expected_total = Decimal('83.00')     # 80 + 8 - 5
        
        self.assertEqual(sales_order.subtotal, expected_subtotal)
        self.assertEqual(sales_order.tax_amount, expected_tax)
        self.assertEqual(sales_order.total_amount, expected_total)


class SalesOrderItemModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.customer = self.create_mock_customer()
        self.quotation = self.create_mock_quotation()
        self.product = self.create_mock_product()
        
        self.sales_order = SalesOrder.objects.create(
            customer=self.customer,
            quotation=self.quotation,
            created_by=self.user
        )

    def create_mock_customer(self):
        from unittest.mock import Mock
        customer = Mock()
        customer.id = 1
        customer.name = 'Test Customer'
        return customer

    def create_mock_quotation(self):
        from unittest.mock import Mock
        quotation = Mock()
        quotation.id = 1
        quotation.quotation_number = 'QUO-2025-000001'
        quotation.customer = self.customer
        return quotation

    def create_mock_product(self):
        from unittest.mock import Mock
        product = Mock()
        product.id = 1
        product.name = 'Test Product'
        product.sku = 'TEST-001'
        return product

    def test_line_total_calculation(self):
        """Test line total calculation with discounts"""
        item = SalesOrderItem.objects.create(
            sales_order=self.sales_order,
            product=self.product,
            quantity=Decimal('3'),
            unit_price=Decimal('20.00'),
            discount_percent=Decimal('10.00')
        )
        
        expected_discount = Decimal('6.00')   # (3 * 20) * 0.10
        expected_total = Decimal('54.00')     # (3 * 20) - 6
        
        self.assertEqual(item.discount_amount, expected_discount)
        self.assertEqual(item.line_total, expected_total)

    def test_item_deletion_updates_order(self):
        """Test that deleting an item updates the order totals"""
        item1 = SalesOrderItem.objects.create(
            sales_order=self.sales_order,
            product=self.product,
            quantity=Decimal('2'),
            unit_price=Decimal('25.00')
        )
        
        item2 = SalesOrderItem.objects.create(
            sales_order=self.sales_order,
            product=self.product,
            quantity=Decimal('1'),
            unit_price=Decimal('30.00')
        )
        
        # Verify initial total
        self.sales_order.refresh_from_db()
        initial_total = self.sales_order.subtotal
        
        # Delete one item
        item1.delete()
        
        # Verify total is updated
        self.sales_order.refresh_from_db()
        self.assertEqual(self.sales_order.subtotal, Decimal('30.00'))


class SalesOrderAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Mock related objects
        self.customer = self.create_mock_customer()
        self.quotation = self.create_mock_quotation()
        self.product = self.create_mock_product()

    def create_mock_customer(self):
        from unittest.mock import Mock
        customer = Mock()
        customer.id = 1
        customer.name = 'Test Customer'
        customer.email = 'customer@test.com'
        return customer

    def create_mock_quotation(self):
        from unittest.mock import Mock
        quotation = Mock()
        quotation.id = 1
        quotation.quotation_number = 'QUO-2025-000001'
        quotation.customer = self.customer
        quotation.status = 'approved'
        return quotation

    def create_mock_product(self):
        from unittest.mock import Mock
        product = Mock()
        product.id = 1
        product.name = 'Test Product'
        product.sku = 'TEST-001'
        return product

    def test_create_sales_order(self):
        """Test creating sales order via API"""
        url = reverse('salesorder-list')
        data = {
            'quotation': self.quotation.id,
            'customer': self.customer.id,
            'tax_rate': '0.15',
            'notes': 'Test order'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SalesOrder.objects.count(), 1)

    def test_create_from_quotation(self):
        """Test creating sales order from quotation"""
        url = reverse('salesorder-create-from-quotation')
        data = {
            'quotation_id': self.quotation.id,
            'expected_delivery_date': '2025-02-01',
            'tax_rate': '0.15',
            'notes': 'Order from quotation'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        sales_order = SalesOrder.objects.first()
        self.assertEqual(sales_order.quotation, self.quotation)
        self.assertEqual(sales_order.created_by, self.user)

    def test_confirm_order(self):
        """Test confirming an order via API"""
        # Create order with items
        sales_order = SalesOrder.objects.create(
            customer=self.customer,
            quotation=self.quotation,
            created_by=self.user
        )
        
        SalesOrderItem.objects.create(
            sales_order=sales_order,
            product=self.product,
            quantity=Decimal('1'),
            unit_price=Decimal('25.00')
        )
        
        url = reverse('salesorder-confirm', kwargs={'pk': sales_order.pk})
        data = {
            'confirmation_notes': 'Order confirmed by customer'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        sales_order.refresh_from_db()
        self.assertEqual(sales_order.status, 'confirmed')
        self.assertIsNotNone(sales_order.confirmed_at)

    def test_cancel_order(self):
        """Test cancelling an order via API"""
        sales_order = SalesOrder.objects.create(
            customer=self.customer,
            quotation=self.quotation,
            created_by=self.user
        )
        
        url = reverse('salesorder-cancel', kwargs={'pk': sales_order.pk})
        data = {
            'reason': 'Customer requested cancellation'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        sales_order.refresh_from_db()
        self.assertEqual(sales_order.status, 'cancelled')

    def test_add_item_to_order(self):
        """Test adding item to order via API"""
        sales_order = SalesOrder.objects.create(
            customer=self.customer,
            quotation=self.quotation,
            created_by=self.user
        )
        
        url = reverse('salesorder-add-item', kwargs={'pk': sales_order.pk})
        data = {
            'product': self.product.id,
            'quantity': '2.000',
            'unit_price': '25.50',
            'discount_percent': '10.00'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(sales_order.items.count(), 1)

    def test_list_orders_with_filters(self):
        """Test listing orders with various filters"""
        # Create test orders
        order1 = SalesOrder.objects.create(
            customer=self.customer,
            quotation=self.quotation,
            created_by=self.user,
            status='draft'
        )
        
        order2 = SalesOrder.objects.create(
            customer=self.customer,
            quotation=self.quotation,
            created_by=self.user,
            status='confirmed'
        )
        
        url = reverse('salesorder-list')
        
        # Test status filter
        response = self.client.get(url, {'status': 'draft'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Test search
        response = self.client.get(url, {'search': order1.order_number})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_bulk_actions(self):
        """Test bulk actions on orders"""
        # Create test orders
        order1 = SalesOrder.objects.create(
            customer=self.customer,
            quotation=self.quotation,
            created_by=self.user
        )
        
        order2 = SalesOrder.objects.create(
            customer=self.customer,
            quotation=self.quotation,
            created_by=self.user
        )
        
        # Add items to make them confirmable
        for order in [order1, order2]:
            SalesOrderItem.objects.create(
                sales_order=order,
                product=self.product,
                quantity=Decimal('1'),
                unit_price=Decimal('25.00')
            )
        
        url = reverse('salesorder-bulk-actions')
        data = {
            'action': 'confirm',
            'order_ids': [order1.id, order2.id]
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify orders were confirmed
        for order in [order1, order2]:
            order.refresh_from_db()
            self.assertEqual(order.status, 'confirmed')

    def test_unauthorized_access(self):
        """Test that unauthorized users cannot access the API"""
        self.client.force_authenticate(user=None)
        
        url = reverse('salesorder-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SalesOrderPermissionTest(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='testpass123'
        )
        
        self.customer = self.create_mock_customer()
        self.quotation = self.create_mock_quotation()
        
        self.sales_order = SalesOrder.objects.create(
            customer=self.customer,
            quotation=self.quotation,
            created_by=self.user1
        )

    def create_mock_customer(self):
        from unittest.mock import Mock
        customer = Mock()
        customer.id = 1
        customer.name = 'Test Customer'
        return customer

    def create_mock_quotation(self):
        from unittest.mock import Mock
        quotation = Mock()
        quotation.id = 1
        quotation.quotation_number = 'QUO-2025-000001'
        quotation.customer = self.customer
        return quotation

    def test_order_edit_permissions(self):
        """Test that only authorized users can edit orders"""
        self.client.force_authenticate(user=self.user2)
        
        url = reverse('salesorder-detail', kwargs={'pk': self.sales_order.pk})
        data = {'notes': 'Updated by user2'}
        
        response = self.client.patch(url, data, format='json')
        
        # Adjust this test based on your permission requirements
        # This example assumes any authenticated user can edit
        self.assertEqual(response.status_code, status.HTTP_200_OK)