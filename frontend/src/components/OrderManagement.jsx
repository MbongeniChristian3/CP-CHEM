import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './OrderManagement.css';

// --- Global Axios Configuration and Interceptor ---
axios.defaults.baseURL = 'http://127.0.0.1:8000/';

// Reusable Modal Component
const Modal = ({ isOpen, onClose, title, children }) => {
    if (!isOpen) return null;

    return createPortal(
        <div className="modal-backdrop">
            <div className="modal-content">
                <div className="modal-header">
                    <h2 className="modal-title">{title}</h2>
                    <button onClick={onClose} className="modal-close-button">
                        <svg xmlns="http://www.w3.org/2000/svg" className="modal-close-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>
                {children}
            </div>
        </div>,
        document.body
    );
};

// Main App Component
const App = () => {
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState('orderList');
    const [orders, setOrders] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState('All');
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [newOrder, setNewOrder] = useState({
        customer: '',
        status: 'Pending',
        paymentStatus: 'Unpaid',
        totalAmount: 0,
        orderDate: new Date().toISOString().slice(0, 10),
    });
    const [error, setError] = useState('');

    // --- Add Axios Interceptor for Token Refresh ---
    useEffect(() => {
        // Set the initial Authorization header
        const accessToken = localStorage.getItem('access_token');
        if (accessToken) {
            axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
        }

        const interceptor = axios.interceptors.response.use(
            response => response,
            async (err) => {
                const originalRequest = err.config;
                // Check if the error is 401 and it's not a retry attempt
                if (err.response.status === 401 && !originalRequest._retry) {
                    originalRequest._retry = true;
                    try {
                        const refreshToken = localStorage.getItem('refresh_token');
                        if (!refreshToken) {
                            navigate('/');
                            return Promise.reject(err);
                        }
                        
                        const res = await axios.post('/api/token/refresh/', {
                            refresh: refreshToken
                        });
                        
                        const newAccessToken = res.data.access;
                        
                        localStorage.setItem('access_token', newAccessToken);
                        axios.defaults.headers.common['Authorization'] = `Bearer ${newAccessToken}`;
                        
                        return axios(originalRequest);
                        
                    } catch (refreshErr) {
                        console.error("Token refresh failed:", refreshErr);
                        localStorage.clear();
                        navigate('/');
                        return Promise.reject(refreshErr);
                    }
                }
                return Promise.reject(err);
            }
        );

        return () => {
            axios.interceptors.response.eject(interceptor);
        };
    }, [navigate]);

    // --- End of Interceptor Logic ---

    // Fetch orders from the API when the component mounts
    useEffect(() => {
        const fetchOrders = async () => {
            try {
                const response = await axios.get('/api/sales-orders/');
                setOrders(response.data);
            } catch (error) {
                console.error('Error fetching orders:', error);
                if (error.response && error.response.status !== 401) {
                    setError('Failed to fetch orders. Please try again.');
                }
            }
        };
        fetchOrders();
    }, []);

    const filteredOrders = orders.filter(order => {
        const matchesSearch = searchTerm === '' ||
            (order.orderNumber && order.orderNumber.toLowerCase().includes(searchTerm.toLowerCase())) ||
            (order.customer && order.customer.toLowerCase().includes(searchTerm.toLowerCase()));
        const matchesStatus = statusFilter === 'All' || order.status === statusFilter;
        return matchesSearch && matchesStatus;
    });

    const handleCreateOrder = async (e) => {
        e.preventDefault();
        setError('');
        try {
            const orderData = {
                customer: newOrder.customer,
                status: newOrder.status,
                payment_status: newOrder.paymentStatus,
                total_amount: parseFloat(newOrder.totalAmount),
                order_date: newOrder.orderDate,
            };

            const response = await axios.post('/api/sales-orders/', orderData);

            setOrders(prevOrders => [...prevOrders, response.data]);
            setIsCreateModalOpen(false);

            setNewOrder({
                customer: '',
                status: 'Pending',
                paymentStatus: 'Unpaid',
                totalAmount: 0,
                orderDate: new Date().toISOString().slice(0, 10),
            });
            
            // Clear filters and search after a successful creation
            setSearchTerm('');
            setStatusFilter('All');

        } catch (error) {
            console.error('Error creating new order:', error);
            if (error.response && error.response.status !== 401) {
                setError('Failed to create order. Please check your data.');
            }
        }
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        if (name === 'totalAmount') {
            setNewOrder(prev => ({ ...prev, [name]: parseFloat(value) || 0 }));
        } else {
            setNewOrder(prev => ({ ...prev, [name]: value }));
        }
    };

    const statusOptions = ['All', 'Pending', 'Shipped', 'Delivered', 'Cancelled'];

    return (
        <div className="app-container">
            <header className="header">
                <h1 className="header-title">Sales Order Management</h1>
                <div className="header-links">
                    <button type="button" className="link">Docs</button>
                    <button type="button" className="link">Help</button>
                </div>
            </header>

            <main className="main-content">
                <div className="card">
                    {/* Tab Navigation */}
                    <div className="tab-navigation">
                        <button
                            onClick={() => setActiveTab('orderList')}
                            className={`tab-button ${activeTab === 'orderList' ? 'tab-active' : ''}`}
                        >
                            Order List
                        </button>
                        <button
                            onClick={() => setIsCreateModalOpen(true)}
                            className="tab-button"
                        >
                            Create Order
                        </button>
                        <button
                            onClick={() => setActiveTab('fromQuotation')}
                            className={`tab-button ${activeTab === 'fromQuotation' ? 'tab-active' : ''}`}
                        >
                            From Quotation
                        </button>
                    </div>

                    {/* Tab Content */}
                    <div className="tab-content">
                        {error && <div className="error-message">{error}</div>}
                        {activeTab === 'orderList' && (
                            <>
                                <div className="filter-controls">
                                    <input
                                        type="text"
                                        placeholder="Search orders..."
                                        value={searchTerm}
                                        onChange={(e) => setSearchTerm(e.target.value)}
                                        className="input-field"
                                    />
                                    <div className="select-wrapper">
                                        <select
                                            value={statusFilter}
                                            onChange={(e) => setStatusFilter(e.target.value)}
                                            className="input-field"
                                        >
                                            {statusOptions.map(status => (
                                                <option key={status} value={status}>{status} Status</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="date-range">
                                        <input type="date" className="input-field" />
                                        <span>-</span>
                                        <input type="date" className="input-field" />
                                    </div>
                                    <button className="search-button">
                                        Search
                                    </button>
                                </div>

                                {/* Order Table */}
                                <div className="table-container">
                                    <table className="order-table">
                                        <thead>
                                            <tr>
                                                <th>Order Number</th>
                                                <th>Customer</th>
                                                <th>Status</th>
                                                <th>Payment Status</th>
                                                <th>Total Amount</th>
                                                <th>Order Date</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {filteredOrders.length > 0 ? (
                                                filteredOrders.map((order) => (
                                                    <tr key={order.id}>
                                                        <td>{order.orderNumber}</td>
                                                        <td>{order.customer}</td>
                                                        <td>
                                                            <span className={`status-badge status-${order.status.toLowerCase()}`}>
                                                                {order.status}
                                                            </span>
                                                        </td>
                                                        <td>{order.paymentStatus}</td>
                                                        <td>${order.totalAmount.toFixed(2)}</td>
                                                        <td>{order.orderDate}</td>
                                                    </tr>
                                                ))
                                            ) : (
                                                <tr>
                                                    <td colSpan="6" className="no-orders-found">
                                                        No orders found.
                                                    </td>
                                                </tr>
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </>
                        )}
                        {activeTab === 'fromQuotation' && (
                            <div className="coming-soon">
                                Functionality to create from a quotation coming soon...
                            </div>
                        )}
                    </div>
                </div>
            </main>

            {/* Create Order Modal */}
            <Modal isOpen={isCreateModalOpen} onClose={() => setIsCreateModalOpen(false)} title="Create New Order">
                <form onSubmit={handleCreateOrder} className="form-container">
                    <div className="form-group">
                        <label htmlFor="customer">Customer</label>
                        <input
                            type="text"
                            name="customer"
                            id="customer"
                            value={newOrder.customer}
                            onChange={handleInputChange}
                            required
                            className="form-input"
                        />
                    </div>
                    <div className="form-group">
                        <label htmlFor="totalAmount">Total Amount</label>
                        <input
                            type="number"
                            name="totalAmount"
                            id="totalAmount"
                            value={newOrder.totalAmount}
                            onChange={handleInputChange}
                            step="0.01"
                            required
                            className="form-input"
                        />
                    </div>
                    <div className="form-group">
                        <label htmlFor="status">Status</label>
                        <select
                            name="status"
                            id="status"
                            value={newOrder.status}
                            onChange={handleInputChange}
                            className="form-input"
                        >
                            {statusOptions.slice(1).map(status => (
                                <option key={status} value={status}>{status}</option>
                            ))}
                        </select>
                    </div>
                    <div className="form-group">
                        <label htmlFor="paymentStatus">Payment Status</label>
                        <select
                            name="paymentStatus"
                            id="paymentStatus"
                            value={newOrder.paymentStatus}
                            onChange={handleInputChange}
                            className="form-input"
                        >
                            <option value="Unpaid">Unpaid</option>
                            <option value="Paid">Paid</option>
                            <option value="Refunded">Refunded</option>
                        </select>
                    </div>
                    <div className="form-actions">
                        <button
                            type="button"
                            onClick={() => setIsCreateModalOpen(false)}
                            className="button-secondary"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            className="button-primary"
                        >
                            Create Order
                        </button>
                    </div>
                </form>
            </Modal>
        </div>
    );
};

export default App;