import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { FileText, Users, Package, ShoppingCart, Truck, Settings, Home, DollarSign, List, TruckIcon, BarChart, ShoppingBag } from 'lucide-react';
import backgroundImage from './background.jpg';

// Color map to correctly apply hex values for a dark theme
const colorMap = {
    'bg-green-500': '#13093fff',
    'bg-purple-500': '#13093fff',
    'bg-orange-500': '#13093fff',
    'bg-indigo-500': '#13093fff',
    'bg-teal-500': '#13093fff',
    'bg-gray-500': '#13093fff',
};

// New Header Component
const Header = ({ userInfo }) => (
    <div style={styles.header}>
        <div style={styles.headerLeft}>
            <h2 style={styles.headerTitle}>WELCOME CP CHEMICALS USER</h2>
            <p style={styles.headerSubtitle}>Multi-Branch Order Management System</p>
        </div>
        <div style={styles.headerRight}>
            <div style={styles.userInfo}>
                <span>Admin</span>
                <span style={styles.userRole}>{userInfo?.username || 'CEO'}</span>
            </div>
            <button style={styles.logoutButton}>Logout</button>
        </div>
    </div>
);

// New Sidebar Component
const Sidebar = () => (
    <div style={styles.sidebar}>
        <div style={styles.logoContainer}>
            {/* Replace with your actual logo */}
            <img src="cplogo.png" alt="CP Chemicals Logo" style={styles.logo} />
            <h3 style={styles.logoText}>Agrochemical OMS</h3>
            <p style={styles.logoSubtitle}>Order Management</p>
        </div>
        <ul style={styles.sidebarMenu}>
            <li style={styles.sidebarMenuItem}>
                <Home size={18} />
                Home
            </li>
            <li style={styles.sidebarMenuItem}>
                <List size={18} />
                Dashboard
            </li>
            <li style={styles.sidebarMenuItem}>
                <DollarSign size={18} />
                POS System
            </li>
            <li style={styles.sidebarMenuItem}>
                <ShoppingBag size={18} />
                Products
            </li>
            <li style={styles.sidebarMenuItem}>
                <ShoppingCart size={18} />
                Orders
            </li>
            <li style={styles.sidebarMenuItem}>
                <TruckIcon size={18} />
                Track Orders
            </li>
            <li style={styles.sidebarMenuItem}>
                <Package size={18} />
                Inventory
            </li>
            <li style={styles.sidebarMenuItem}>
                <BarChart size={18} />
                Reports
            </li>
        </ul>
    </div>
);

const Homepage = () => {
    const navigate = useNavigate();
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [userInfo, setUserInfo] = useState(null);

    // Static module data with routes
    const modules = [
        {
            id: 'quotations',
            name: 'Quotations',
            description: 'Create and manage customer quotations.',
            icon: FileText,
            route: '/quotations',
            color: 'bg-green-500'
        },
        {
            id: 'customers',
            name: 'Customers',
            description: 'Manage customer information and relationships.',
            icon: Users,
            route: '/customers',
            color: 'bg-purple-500'
        },
        {
            id: 'orders',
            name: 'Orders',
            description: 'Process and track customer orders.',
            icon: ShoppingCart,
            route: '/orders',
            color: 'bg-orange-500'
        },
        {
            id: 'inventory',
            name: 'Inventory',
            description: 'Track stock levels and manage warehouse.',
            icon: Package,
            route: '/inventory',
            color: 'bg-indigo-500'
        },
        {
            id: 'shipping',
            name: 'Shipping',
            description: 'Manage deliveries and logistics.',
            icon: Truck,
            route: '/shipping',
            color: 'bg-teal-500'
        },
        {
            id: 'settings',
            name: 'Settings',
            description: 'System configuration and preferences.',
            icon: Settings,
            route: '/settings',
            color: 'bg-gray-500'
        }
    ];

    useEffect(() => {
        const token = localStorage.getItem('access_token');
        const userString = localStorage.getItem('user');

        if (token && userString) {
            try {
                const user = JSON.parse(userString);
                setUserInfo(user);
                setIsAuthenticated(true);
            } catch (error) {
                console.error('Error parsing user data:', error);
                setIsAuthenticated(false);
                navigate('/login');
            }
        } else {
            setIsAuthenticated(false);
            navigate('/login');
        }
    }, [navigate]);

    const handleModuleClick = async (module) => {
        if (module.id === 'quotations') {
            const token = localStorage.getItem('access_token');

            if (!token) {
                alert('Authentication token not found. Please log in again.');
                navigate('/login');
                return;
            }

            try {
                const response = await axios.get(
                    'http://127.0.0.1:8000/api/quotations/',
                    {
                        headers: {
                            Authorization: `Bearer ${token}`
                        }
                    }
                );
                console.log('Quotations data:', response.data);
                navigate(module.route, { state: { quotations: response.data } });
            } catch (error) {
                console.error('Failed to fetch quotations:', error);
                if (error.response && error.response.status === 401) {
                    alert('Session expired or unauthorized. Please log in.');
                    navigate('/login');
                } else {
                    alert('Failed to load quotations. Please try again.');
                }
            }
        } else if (module.route) {
            navigate(module.route);
        } else {
            alert(`${module.name} module is coming soon!`);
        }
    };

    if (!isAuthenticated) {
        return (
            <div style={styles.loadingContainer}>
                <div>Loading...</div>
            </div>
        );
    }

    return (
        <div style={styles.mainContainer}>
            <Sidebar />
            <div style={styles.contentContainer}>
                <Header userInfo={userInfo} />
                <div style={styles.homepageContainer}>
                    <header style={styles.homepageHeader}>
                        <h1 style={styles.homepageHeaderH1}>Welcome, {userInfo?.username || 'User'}!</h1>
                        <p style={styles.homepageHeaderP}>Choose a module to get started</p>
                    </header>
                    <main style={styles.modulesGrid}>
                        {modules.map((module) => {
                            const IconComponent = module.icon;
                            return (
                                <div
                                    key={module.id}
                                    onClick={() => handleModuleClick(module)}
                                    style={{ ...styles.moduleCard, backgroundColor: colorMap[module.color] }}
                                >
                                    <IconComponent style={styles.moduleIcon} />
                                    <h3 style={styles.moduleCardH3}>{module.name}</h3>
                                    <p style={styles.moduleCardP}>{module.description}</p>
                                </div>
                            );
                        })}
                    </main>
                </div>
            </div>
        </div>
    );
};

// CSS-in-JS object for styling
const styles = {
    mainContainer: {
        display: 'flex',
        minHeight: '100vh',
        backgroundColor: '#13093fff',
    },
    sidebar: {
        width: '200px',
        backgroundColor: '#212121',
        color: 'white',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        fontFamily: 'Arial, sans-serif',
    },
    logoContainer: {
        textAlign: 'center',
        marginBottom: '30px',
    },
    logo: {
        width: '80px',
        marginBottom: '10px',
    },
    logoText: {
        fontSize: '1.1rem',
        fontWeight: 'bold',
        color: '#fff',
        margin: '0',
    },
    logoSubtitle: {
        fontSize: '0.7rem',
        color: '#bdbdbd',
        margin: '0',
    },
    sidebarMenu: {
        listStyle: 'none',
        padding: '0',
        width: '100%',
    },
    sidebarMenuItem: {
        display: 'flex',
        alignItems: 'center',
        padding: '10px 15px',
        margin: '5px 0',
        borderRadius: '8px',
        cursor: 'pointer',
        transition: 'background-color 0.2s',
        gap: '10px',
        '&:hover': {
            backgroundColor: '#3a3a3a',
        },
    },
    contentContainer: {
        flexGrow: '1',
        display: 'flex',
        flexDirection: 'column',
    },
    header: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '20px 40px',
        backgroundColor: '#212121',
        color: 'white',
        borderBottom: '1px solid #444',
        fontFamily: 'Arial, sans-serif',
        position: 'sticky',
        top: '0',
        zIndex: '1000',
    },
    headerLeft: {
        textAlign: 'left',
    },
    headerTitle: {
        margin: '0',
        fontSize: '1.5rem',
        color: '#fff',
    },
    headerSubtitle: {
        margin: '0',
        fontSize: '0.9rem',
        color: '#bdbdbd',
    },
    headerRight: {
        display: 'flex',
        alignItems: 'center',
        gap: '20px',
    },
    userInfo: {
        display: 'flex',
        flexDirection: 'column',
        textAlign: 'right',
    },
    userRole: {
        fontSize: '0.8rem',
        color: '#bdbdbd',
    },
    logoutButton: {
        padding: '8px 15px',
        backgroundColor: '#555',
        color: 'white',
        border: 'none',
        borderRadius: '5px',
        cursor: 'pointer',
        '&:hover': {
            backgroundColor: '#777',
        },
    },
    homepageContainer: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        padding: '40px',
        fontFamily: 'Arial, sans-serif',
        backgroundColor: '#597e52ff',
        minHeight: '100vh',
        color: '#e0e0e0',
        backgroundImage: `url(${backgroundImage})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        backgroundAttachment: 'fixed',
    },
    loadingContainer: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        backgroundColor: '#B4D334',
        color: '#e0e0e0',
    },
    homepageHeader: {
        textAlign: 'center',
        marginBottom: '40px',
        backgroundColor: 'rgba(0, 0, 0, 0.4)',
        padding: '10px 20px',
        borderRadius: '10px'
    },
    homepageHeaderH1: {
        fontSize: '2.5rem',
        color: 'white',
        margin: '0',
    },
    homepageHeaderP: {
        fontSize: '1.1rem',
        color: '#bdbdbd',
    },
    modulesGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: '25px',
        width: '100%',
        maxWidth: '1200px',
    },
    moduleCard: {
        padding: '30px',
        borderRadius: '12px',
        color: 'white',
        textAlign: 'center',
        transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
        cursor: 'pointer',
        boxShadow: '0 4px 8px rgba(0, 0, 0, 0.2)',
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
    },
    moduleIcon: {
        width: '50px',
        height: '50px',
        marginBottom: '15px',
        color: 'white',
    },
    moduleCardH3: {
        fontSize: '1.5rem',
        margin: '0 0 10px 0',
    },
    moduleCardP: {
        fontSize: '1rem',
        margin: '0',
        color: '#f0f0f0',
    },
};

export default Homepage;