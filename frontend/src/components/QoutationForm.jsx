import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Plus, Trash2, Calculator, Save, Send, FileText, AlertCircle } from 'lucide-react';

// Configure axios to match your existing setup
axios.defaults.baseURL = 'http://127.0.0.1:8000//';
axios.defaults.headers.post['Content-Type'] = 'application/json';

const QuotationForm = () => {
  // Form state management
  const [quotationData, setQuotationData] = useState({
    customer_name: '',
    customer_email: '',
    customer_phone: '',
    customer_address: '',
    notes: '',
    valid_until: '',
    discount_percentage: 0,
    tax_percentage: 15, // Default tax rate
    status: 'draft'
  });

  const [quotationItems, setQuotationItems] = useState([
    {
      id: Date.now(),
      product_id: '',
      product_name: '',
      description: '',
      quantity: 1,
      unit_price: 0,
      total_price: 0
    }
  ]);

  const [calculations, setCalculations] = useState({
    subtotal: 0,
    discount_amount: 0,
    tax_amount: 0,
    total_amount: 0
  });

  // State for products and authentication
  const [availableProducts, setAvailableProducts] = useState([]);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userInfo, setUserInfo] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [alert, setAlert] = useState({ type: '', message: '' });

  // Check authentication and load initial data
  useEffect(() => {
    checkAuthentication();
    loadProducts();
  }, []);

  // Check if user is authenticated using your token system
  const checkAuthentication = () => {
    const token = localStorage.getItem('access_token') || localStorage.getItem('token');
    const userString = localStorage.getItem('user');
    
    if (token && userString) {
      try {
        const user = JSON.parse(userString);
        setUserInfo(user);
        setIsAuthenticated(true);
        
        // Add token to axios headers for API calls
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      } catch (error) {
        console.error('Error parsing user data:', error);
        setAlert({ type: 'error', message: 'Authentication error. Please login again.' });
      }
    } else {
      setAlert({ type: 'error', message: 'Please login to create quotations.' });
    }
  };

  // Load products from your Django API
  const loadProducts = async () => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      if (!token) {
        console.log('No auth token available');
        return;
      }

      const response = await axios.get('/api/products/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.data && response.data.results) {
        setAvailableProducts(response.data.results);
      } else if (Array.isArray(response.data)) {
        setAvailableProducts(response.data);
      }
    } catch (error) {
      console.error('Error loading products:', error);
      // Set sample products as fallback
      setAvailableProducts([
        { id: '1', name: 'Sulfuric Acid H2SO4', price: 25.99, sku: 'CHEM-001' },
        { id: '2', name: 'Sodium Chloride NaCl', price: 15.50, sku: 'CHEM-002' },
        { id: '3', name: 'Calcium Carbonate CaCO3', price: 18.75, sku: 'CHEM-003' },
        { id: '4', name: 'Hydrochloric Acid HCl', price: 22.00, sku: 'CHEM-004' },
        { id: '5', name: 'Potassium Hydroxide KOH', price: 28.50, sku: 'CHEM-005' }
      ]);
    }
  };

  // Calculate totals whenever items or percentages change
  useEffect(() => {
    const subtotal = quotationItems.reduce((sum, item) => sum + item.total_price, 0);
    const discount_amount = (subtotal * quotationData.discount_percentage) / 100;
    const amount_after_discount = subtotal - discount_amount;
    const tax_amount = (amount_after_discount * quotationData.tax_percentage) / 100;
    const total_amount = amount_after_discount + tax_amount;

    setCalculations({
      subtotal: parseFloat(subtotal.toFixed(2)),
      discount_amount: parseFloat(discount_amount.toFixed(2)),
      tax_amount: parseFloat(tax_amount.toFixed(2)),
      total_amount: parseFloat(total_amount.toFixed(2))
    });
  }, [quotationItems, quotationData.discount_percentage, quotationData.tax_percentage]);

  // Show alert messages
  const showAlert = (type, message) => {
    setAlert({ type, message });
    setTimeout(() => {
      setAlert({ type: '', message: '' });
    }, 5000);
  };

  // Handle form field changes
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setQuotationData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Handle item changes
  const handleItemChange = (index, field, value) => {
    const updatedItems = [...quotationItems];
    updatedItems[index][field] = value;

    // Auto-calculate total price when quantity or unit price changes
    if (field === 'quantity' || field === 'unit_price') {
      const quantity = parseFloat(updatedItems[index].quantity) || 0;
      const unitPrice = parseFloat(updatedItems[index].unit_price) || 0;
      updatedItems[index].total_price = parseFloat((quantity * unitPrice).toFixed(2));
    }

    // Auto-populate product details when product is selected
    if (field === 'product_id') {
      const selectedProduct = availableProducts.find(p => p.id === value);
      if (selectedProduct) {
        updatedItems[index].product_name = selectedProduct.name;
        updatedItems[index].unit_price = selectedProduct.price;
        const quantity = parseFloat(updatedItems[index].quantity) || 0;
        updatedItems[index].total_price = parseFloat((quantity * selectedProduct.price).toFixed(2));
      }
    }

    setQuotationItems(updatedItems);
  };

  // Add new item row
  const addItem = () => {
    setQuotationItems([
      ...quotationItems,
      {
        id: Date.now(),
        product_id: '',
        product_name: '',
        description: '',
        quantity: 1,
        unit_price: 0,
        total_price: 0
      }
    ]);
  };

  // Remove item row
  const removeItem = (index) => {
    if (quotationItems.length > 1) {
      setQuotationItems(quotationItems.filter((_, i) => i !== index));
    }
  };

  // Handle form submission using your Django API
  const handleSubmit = async (status = 'draft') => {
    if (!isAuthenticated) {
      showAlert('error', 'Please login to create quotations.');
      return;
    }

    setIsSubmitting(true);
    
    try {
      // Validate required fields
      if (!quotationData.customer_name || !quotationData.customer_email) {
        showAlert('error', 'Please fill in customer name and email');
        return;
      }

      if (quotationItems.some(item => !item.product_id || item.quantity <= 0)) {
        showAlert('error', 'Please ensure all items have valid products and quantities');
        return;
      }

      // Set default valid_until date if not provided (30 days from now)
      const validUntil = quotationData.valid_until || 
        new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

      const submissionData = {
        customer_name: quotationData.customer_name,
        customer_email: quotationData.customer_email,
        customer_phone: quotationData.customer_phone,
        customer_address: quotationData.customer_address,
        notes: quotationData.notes,
        valid_until: validUntil,
        status: status,
        discount_percentage: quotationData.discount_percentage,
        tax_percentage: quotationData.tax_percentage,
        total_amount: calculations.subtotal,
        discount_amount: calculations.discount_amount,
        tax_amount: calculations.tax_amount,
        final_amount: calculations.total_amount,
        items: quotationItems.filter(item => item.product_id).map(item => ({
          product_id: item.product_id,
          quantity: parseInt(item.quantity),
          unit_price: parseFloat(item.unit_price),
          total_price: parseFloat(item.total_price),
          description: item.description || ''
        }))
      };

      console.log('Submitting quotation data:', submissionData);
      
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      
      const response = await axios.post('/api/quotations/', submissionData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.data.success) {
        showAlert('success', `Quotation ${status === 'draft' ? 'saved as draft' : 'submitted'} successfully!`);
        
        // Clear form after successful submission
        setQuotationData({
          customer_name: '',
          customer_email: '',
          customer_phone: '',
          customer_address: '',
          notes: '',
          valid_until: '',
          discount_percentage: 0,
          tax_percentage: 15,
          status: 'draft'
        });
        
        setQuotationItems([
          {
            id: Date.now(),
            product_id: '',
            product_name: '',
            description: '',
            quantity: 1,
            unit_price: 0,
            total_price: 0
          }
        ]);
        
      } else {
        throw new Error(response.data.message || 'Failed to create quotation');
      }
      
    } catch (error) {
      console.error('Error submitting quotation:', error);
      
      if (error.response) {
        // Server responded with error status
        const errorData = error.response.data;
        showAlert('error', errorData.message || `Error ${error.response.status}: Failed to create quotation`);
      } else if (error.request) {
        // Request was made but no response received
        showAlert('error', 'Failed to connect to server. Please check your connection.');
      } else {
        // Something else happened
        showAlert('error', error.message || 'An unexpected error occurred');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6 bg-white shadow-lg rounded-lg">
      {/* Authentication Check */}
      {!isAuthenticated ? (
        <div className="text-center py-12">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Authentication Required</h2>
          <p className="text-gray-600 mb-6">Please login to create quotations.</p>
          <button 
            onClick={() => window.location.href = '/login'} 
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Go to Login
          </button>
        </div>
      ) : (
        <>
          {/* Alert Messages */}
          {alert.message && (
            <div className={`mb-6 p-4 rounded-lg ${
              alert.type === 'success' 
                ? 'bg-green-50 text-green-800 border border-green-200' 
                : 'bg-red-50 text-red-800 border border-red-200'
            }`}>
              <div className="flex items-center">
                <AlertCircle className="w-5 h-5 mr-2" />
                {alert.message}
              </div>
            </div>
          )}

          {/* Header */}
          <div className="border-b border-gray-200 pb-6 mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Create Quotation</h1>
                <p className="text-gray-600 mt-1">
                  Generate professional quotes for your customers
                  {userInfo && userInfo.warehouse && (
                    <span className="text-sm text-blue-600 ml-2">
                      • {userInfo.warehouse} Warehouse
                    </span>
                  )}
                </p>
              </div>
              <FileText className="w-12 h-12 text-blue-600" />
            </div>
          </div>

          {/* Customer Information */}
          <div className="bg-gray-50 rounded-lg p-6 mb-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Customer Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Customer Name *
                </label>
                <input
                  type="text"
                  name="customer_name"
                  value={quotationData.customer_name}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter customer name"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email Address *
                </label>
                <input
                  type="email"
                  name="customer_email"
                  value={quotationData.customer_email}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="customer@example.com"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Phone Number
                </label>
                <input
                  type="tel"
                  name="customer_phone"
                  value={quotationData.customer_phone}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="+27 11 123 4567"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Valid Until
                </label>
                <input
                  type="date"
                  name="valid_until"
                  value={quotationData.valid_until}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  min={new Date().toISOString().split('T')[0]}
                />
              </div>
            </div>
            <div className="mt-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Customer Address
              </label>
              <textarea
                name="customer_address"
                value={quotationData.customer_address}
                onChange={handleInputChange}
                rows={3}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter complete customer address"
              />
            </div>
          </div>

          {/* Quotation Items */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-800">Quotation Items</h2>
              <button
                type="button"
                onClick={addItem}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                <Plus className="w-4 h-4" />
                Add Item
              </button>
            </div>

            {/* Items Table */}
            <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Product
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Description
                      </th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Qty
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Unit Price
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Total
                      </th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Action
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {quotationItems.map((item, index) => (
                      <tr key={item.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <select
                            value={item.product_id}
                            onChange={(e) => handleItemChange(index, 'product_id', e.target.value)}
                            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          >
                            <option value="">Select Product</option>
                            {availableProducts.map(product => (
                              <option key={product.id} value={product.id}>
                                {product.name} {product.sku && `(${product.sku})`}
                              </option>
                            ))}
                          </select>
                        </td>
                        <td className="px-4 py-3">
                          <input
                            type="text"
                            value={item.description}
                            onChange={(e) => handleItemChange(index, 'description', e.target.value)}
                            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="Additional notes..."
                          />
                        </td>
                        <td className="px-4 py-3">
                          <input
                            type="number"
                            value={item.quantity}
                            onChange={(e) => handleItemChange(index, 'quantity', e.target.value)}
                            min="1"
                            className="w-20 px-3 py-2 text-sm text-center border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          />
                        </td>
                        <td className="px-4 py-3 text-right">
                          <input
                            type="number"
                            value={item.unit_price}
                            onChange={(e) => handleItemChange(index, 'unit_price', e.target.value)}
                            min="0"
                            step="0.01"
                            className="w-24 px-3 py-2 text-sm text-right border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          />
                        </td>
                        <td className="px-4 py-3 text-right font-semibold">
                          R {item.total_price.toFixed(2)}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <button
                            type="button"
                            onClick={() => removeItem(index)}
                            disabled={quotationItems.length === 1}
                            className="p-2 text-red-600 hover:bg-red-50 rounded-md disabled:text-gray-400 disabled:cursor-not-allowed"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Calculations */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            {/* Notes */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Notes & Terms
              </label>
              <textarea
                name="notes"
                value={quotationData.notes}
                onChange={handleInputChange}
                rows={6}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Payment terms, delivery conditions, or special notes..."
              />
            </div>

            {/* Totals */}
            <div className="bg-gray-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <Calculator className="w-5 h-5" />
                Quotation Summary
              </h3>
              
              {/* Discount */}
              <div className="flex items-center justify-between mb-3">
                <label className="text-sm font-medium text-gray-700">
                  Discount (%)
                </label>
                <input
                  type="number"
                  name="discount_percentage"
                  value={quotationData.discount_percentage}
                  onChange={handleInputChange}
                  min="0"
                  max="100"
                  step="0.1"
                  className="w-20 px-3 py-1 text-sm text-right border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Tax */}
              <div className="flex items-center justify-between mb-4">
                <label className="text-sm font-medium text-gray-700">
                  Tax (%)
                </label>
                <input
                  type="number"
                  name="tax_percentage"
                  value={quotationData.tax_percentage}
                  onChange={handleInputChange}
                  min="0"
                  max="100"
                  step="0.1"
                  className="w-20 px-3 py-1 text-sm text-right border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <hr className="my-4" />

              {/* Calculation Summary */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Subtotal:</span>
                  <span>R {calculations.subtotal.toFixed(2)}</span>
                </div>
                {calculations.discount_amount > 0 && (
                  <div className="flex justify-between text-sm text-green-600">
                    <span>Discount ({quotationData.discount_percentage}%):</span>
                    <span>-R {calculations.discount_amount.toFixed(2)}</span>
                  </div>
                )}
                <div className="flex justify-between text-sm">
                  <span>Tax ({quotationData.tax_percentage}%):</span>
                  <span>R {calculations.tax_amount.toFixed(2)}</span>
                </div>
                <hr className="my-2" />
                <div className="flex justify-between text-lg font-bold">
                  <span>Total Amount:</span>
                  <span className="text-blue-600">R {calculations.total_amount.toFixed(2)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-end">
            <button
              type="button"
              onClick={() => handleSubmit('draft')}
              disabled={isSubmitting}
              className="flex items-center justify-center gap-2 px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save className="w-4 h-4" />
              {isSubmitting ? 'Saving...' : 'Save as Draft'}
            </button>
            <button
              type="button"
              onClick={() => handleSubmit('sent')}
              disabled={isSubmitting}
              className="flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-4 h-4" />
              {isSubmitting ? 'Sending...' : 'Send Quotation'}
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default QuotationForm;