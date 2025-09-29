import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LoginForm from './components/LoginForm';
import Homepage from './components/Homepage';
import SalesOrderManagement from './components/OrderManagement';
import ProductForm from './components/ProductForm'; // 👈 Import the new component

function App() {
  // Dummy functions to pass to ProductForm since it expects props
  const handleProductCreated = (newProduct) => {
    console.log('New product created and handled by App:', newProduct);
    alert(`Product "${newProduct.name}" was successfully added!`);
    // In a real app, you'd likely update a list of products here
  };

  const handleCancel = () => {
    console.log('Product form cancelled');
    // In a real app, you'd likely navigate the user back to a product list page
    alert('Product creation cancelled.');
  };

  return (
    <Router>
      <div className="App">
        <Routes>
          {/* Default route is now the Login page */}
          <Route path="/" element={<LoginForm />} />
          
          {/* The Dashboard/Homepage is now a protected route */}
          <Route path="/dashboard" element={<Homepage />} />
          
          {/* New route for Sales Order Management */}
          <Route path="/sales-orders" element={<SalesOrderManagement />} />
          
          {/* 🚀 New route for adding products */}
          <Route
            path="/add-product"
            element={
              <ProductForm
                onProductCreated={handleProductCreated}
                onCancel={handleCancel}
              />
            }
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;