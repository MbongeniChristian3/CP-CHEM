import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './ProductForm.css'; // Assuming you have a CSS file for styling
import { useNavigate } from 'react-router-dom'; // Import useNavigate for redirection

// This configuration will be handled within the component's useEffect
axios.defaults.baseURL = 'http://127.0.0.1:8000/';

// --- Sub-component: ProductForm ---
const ProductForm = ({ onProductCreated, onCancel }) => {
    const [productData, setProductData] = useState({
        name: '',
        description: '',
        price: '',
        sku: '',
        category: '',
        manufacturer: '',
    });

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setProductData(prevData => ({ ...prevData, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const response = await axios.post('/api/products/', productData);
            console.log('Product created successfully:', response.data);
            onProductCreated(response.data);
            setProductData({
                name: '', description: '', price: '', sku: '',
                category: '', manufacturer: '',
            });
        } catch (err) {
            console.error('Error creating product:', err.response || err);
            // The axios interceptor will handle the 401 error,
            // so this block can be simplified.
            if (err.response && err.response.status !== 401) {
                setError('Failed to create product. Please check your data and try again.');
            } else if (err.request && !err.response) {
                setError('Network error. Please try again.');
            } else if (err.response && err.response.status === 400) {
                setError(err.response.data.message || 'Validation error. Please check your inputs.');
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="product-form-modal">
            <h3>Add a New Product</h3>
            <div className="form-group">
                <label htmlFor="name">Product Name</label>
                <input type="text" name="name" value={productData.name} onChange={handleInputChange} required />
            </div>
            <div className="form-group">
                <label htmlFor="manufacturer">Manufacturer</label>
                <input type="text" name="manufacturer" value={productData.manufacturer} onChange={handleInputChange} required />
            </div>
            <div className="form-group">
                <label htmlFor="description">Description</label>
                <textarea name="description" value={productData.description} onChange={handleInputChange} />
            </div>
            <div className="form-group">
                <label htmlFor="category">Category</label>
                <input type="text" name="category" value={productData.category} onChange={handleInputChange} required />
            </div>
            <div className="form-group">
                <label htmlFor="price">Price</label>
                <input type="number" name="price" value={productData.price} onChange={handleInputChange} step="0.01" required />
            </div>
            <div className="form-group">
                <label htmlFor="sku">SKU</label>
                <input type="text" name="sku" value={productData.sku} onChange={handleInputChange} required />
            </div>
            
            {error && <div className="error-message">{error}</div>}
            
            <div className="form-actions">
                <button type="submit" className="button-primary" disabled={loading}>
                    {loading ? 'Adding...' : 'Add Product'}
                </button>
                <button type="button" onClick={onCancel} className="button-secondary">
                    Cancel
                </button>
            </div>
        </form>
    );
};

// --- Sub-component: ProductList ---
const ProductList = ({ products, loading }) => {
    if (loading) {
        return <div className="loading-state">Loading products...</div>;
    }
    
    if (products.length === 0) {
        return <div className="empty-state">No products found.</div>;
    }

    return (
        <div className="product-list-grid">
            <div className="product-header">
                <div>Name / SKU</div>
                <div>Manufacturer</div>
                <div>Description</div>
                <div>Category</div>
                <div>Pricing</div>
            </div>
            {products.map(product => (
                <div key={product.sku} className="product-row">
                    <div className="product-name-sku">
                        <strong>{product.name}</strong>
                        <span className="sku-text">SKU: {product.sku}</span>
                    </div>
                    <div className="product-manufacturer">{product.manufacturer}</div>
                    <div className="product-description">{product.description}</div>
                    <div className="product-category">{product.category}</div>
                    <div className="product-pricing">
                        <span>{product.price ? `$${product.price}` : 'No pricing'}</span>
                    </div>
                </div>
            ))}
        </div>
    );
};

// --- Sub-component: SearchFilterBar ---
const SearchFilterBar = ({ searchQuery, onSearchChange, selectedCategory, onCategoryChange, onClearFilters, onAddProductClick }) => (
    <div className="search-filter-bar">
        <div className="search-input-group">
            <label className="input-label">Search Products</label>
            <input 
                type="text" 
                placeholder="Search by name or SKU..."
                value={searchQuery}
                onChange={(e) => onSearchChange(e.target.value)}
            />
        </div>
        <div className="category-select-group">
            <label className="input-label">Category</label>
            <select value={selectedCategory} onChange={(e) => onCategoryChange(e.target.value)}>
                <option value="All Categories">All Categories</option>
                <option value="Herbicides">Herbicides</option>
                <option value="Insecticides">Insecticides</option>
                {/* Add more options as needed */}
            </select>
        </div>
        <div className="filter-buttons">
            <button onClick={onClearFilters} className="button-secondary">Clear Filters</button>
            <button onClick={onAddProductClick} className="button-primary">Add Product</button>
        </div>
    </div>
);

// --- Main Component: ProductCatalog ---
const ProductCatalog = () => {
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('All Categories');
    const [isFormVisible, setIsFormVisible] = useState(false);
    const navigate = useNavigate();

    // 1. Centralize the Axios Token Setup and Interceptor logic
    useEffect(() => {
        // Set the initial authorization header
        const initialToken = localStorage.getItem('access_token');
        if (initialToken) {
            axios.defaults.headers.common['Authorization'] = `Bearer ${initialToken}`;
        }
        
        // Setup the axios response interceptor
        const interceptor = axios.interceptors.response.use(
            response => response,
            async (err) => {
                const originalRequest = err.config;
                if (err.response.status === 401 && !originalRequest._retry) {
                    originalRequest._retry = true;
                    try {
                        const refreshToken = localStorage.getItem('refresh_token');
                        if (!refreshToken) {
                            // No refresh token, force user to log in
                            navigate('/');
                            return Promise.reject(err);
                        }
                        
                        // Request a new access token
                        const res = await axios.post('/api/token/refresh/', {
                            refresh: refreshToken
                        });
                        
                        const newAccessToken = res.data.access;
                        
                        // Update local storage and the axios header with the new token
                        localStorage.setItem('access_token', newAccessToken);
                        axios.defaults.headers.common['Authorization'] = `Bearer ${newAccessToken}`;
                        
                        // Retry the original request with the new token
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

        // Clean up the interceptor when the component unmounts
        return () => {
            axios.interceptors.response.eject(interceptor);
        };
    }, [navigate]);

    const fetchProducts = useCallback(async () => {
        setLoading(true);
        try {
            const params = {};
            if (searchQuery) {
                params.search = searchQuery;
            }
            if (selectedCategory !== 'All Categories') {
                params.category = selectedCategory;
            }
            const response = await axios.get('/api/products/', { params });
            setProducts(response.data);
        } catch (error) {
            console.error('Error fetching products:', error);
            // The interceptor will handle the 401, so we don't need a specific check here
            setProducts([]); 
        } finally {
            setLoading(false);
        }
    }, [searchQuery, selectedCategory]);

    useEffect(() => {
        const delayDebounceFn = setTimeout(() => {
            fetchProducts();
        }, 500);
        return () => clearTimeout(delayDebounceFn);
    }, [fetchProducts]);

    const handleProductCreated = (newProduct) => {
        setIsFormVisible(false);
        fetchProducts();
    };

    return (
        <div className="product-catalog-page">
            <div className="header-bar">
                <h1>Product Catalog</h1>
                <p>Manage your product inventory</p>
            </div>
            <SearchFilterBar
                searchQuery={searchQuery}
                onSearchChange={setSearchQuery}
                selectedCategory={selectedCategory}
                onCategoryChange={setSelectedCategory}
                onClearFilters={() => { setSearchQuery(''); setSelectedCategory('All Categories'); }}
                onAddProductClick={() => setIsFormVisible(true)}
            />
            {isFormVisible && (
                <div className="modal-overlay">
                    <ProductForm 
                        onProductCreated={handleProductCreated} 
                        onCancel={() => setIsFormVisible(false)} 
                    />
                </div>
            )}
            <ProductList products={products} loading={loading} />
        </div>
    );
};

export default ProductCatalog;