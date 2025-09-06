import React, { useState } from 'react';
import axios from 'axios';
import './LoginForm.css';

// Configure axios defaults
axios.defaults.baseURL = 'http://127.0.0.1:8000/';
axios.defaults.headers.post['Content-Type'] = 'application/json';

const LoginForm = () => {
    const [view, setView] = useState('login');
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [firstName, setFirstName] = useState('');
    const [lastName, setLastName] = useState('');
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleLogin = async (e) => {
        e.preventDefault();
        setError('');
        setMessage('');
        setLoading(true);
        
        try {
            const response = await axios.post('/api/login/', {
                username,
                password
            });
            
            const data = response.data;
            
            if (data.success) {
                console.log('Login successful:', data);
                setMessage('Login successful! Welcome.');
                
                // Store tokens in localStorage
                if (data.tokens) {
                    localStorage.setItem('access_token', data.tokens.access);
                    localStorage.setItem('refresh_token', data.tokens.refresh);
                }
                
                // Store user data
                localStorage.setItem('user', JSON.stringify(data.user));
                
                // Optional: Redirect to dashboard
                // window.location.href = '/dashboard';
            } else {
                throw new Error(data.message || 'Login failed');
            }
        } catch (err) {
            console.error('Login error:', err);
            
            // Handle different types of errors
            if (err.response) {
                // Server responded with error status
                const errorData = err.response.data;
                setError(errorData.message || `Login failed: ${err.response.status}`);
            } else if (err.request) {
                // Request was made but no response received
                setError('Failed to connect to server. Please check if the server is running.');
            } else {
                // Something else happened
                setError(err.message || 'An unexpected error occurred');
            }
        } finally {
            setLoading(false);
        }
    };

    const handleRegister = async (e) => {
        e.preventDefault();
        setError('');
        setMessage('');
        setLoading(true);
        
        try {
            const response = await axios.post('/api/register/', {
                username,
                email,
                password,
                first_name: firstName,
                last_name: lastName
            });
            
            const data = response.data;
            
            if (data.success) {
                console.log('Registration successful:', data);
                setMessage('Registration successful! Please log in.');
                setView('login');
                // Clear form fields
                setUsername('');
                setEmail('');
                setPassword('');
                setFirstName('');
                setLastName('');
            } else {
                throw new Error(data.message || 'Registration failed');
            }
        } catch (err) {
            console.error('Registration error:', err);
            
            // Handle different types of errors
            if (err.response) {
                // Server responded with error status
                const errorData = err.response.data;
                setError(errorData.message || `Registration failed: ${err.response.status}`);
            } else if (err.request) {
                // Request was made but no response received
                setError('Failed to connect to server. Please check if the server is running.');
            } else {
                // Something else happened
                setError(err.message || 'An unexpected error occurred');
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className='wrapper'>
            <form onSubmit={view === 'login' ? handleLogin : handleRegister} className='form-box'>
                <h1>{view === 'login' ? 'Login' : 'Register'}</h1>
                
                {error && (
                    <div className="alert alert-danger" role="alert">
                        {error}
                    </div>
                )}
                {message && (
                    <div className="alert alert-success" role="alert">
                        {message}
                    </div>
                )}

                {/* Username Input Group */}
                <div className='form-group'>
                    <label htmlFor="username">Username</label>
                    <div className='input-box'>
                        <input
                            type="text"
                            id="username"
                            required
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="Enter your username"
                        />
                    </div>
                </div>

                {/* Email Input Group - Only for Registration */}
                {view === 'register' && (
                    <>
                        <div className='form-group'>
                            <label htmlFor="email">Email</label>
                            <div className='input-box'>
                                <input
                                    type="email"
                                    id="email"
                                    required
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="Enter your email"
                                />
                            </div>
                        </div>
                        <div className='form-group'>
                            <label htmlFor="firstName">First Name</label>
                            <div className='input-box'>
                                <input
                                    type="text"
                                    id="firstName"
                                    value={firstName}
                                    onChange={(e) => setFirstName(e.target.value)}
                                    placeholder="Enter your first name"
                                />
                            </div>
                        </div>
                        <div className='form-group'>
                            <label htmlFor="lastName">Last Name</label>
                            <div className='input-box'>
                                <input
                                    type="text"
                                    id="lastName"
                                    value={lastName}
                                    onChange={(e) => setLastName(e.target.value)}
                                    placeholder="Enter your last name"
                                />
                            </div>
                        </div>
                    </>
                )}

                {/* Password Input Group */}
                <div className='form-group'>
                    <label htmlFor="password">Password</label>
                    <div className='input-box'>
                        <input
                            type="password"
                            id="password"
                            required
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Enter your password"
                        />
                    </div>
                </div>

                {/* Remember Me & Login Button */}
                <div className="remember-forget">
                    {view === 'login' && (
                        <label>
                            <input type="checkbox"/>
                            Remember me
                        </label>
                    )}
                    <button type='submit' className='btn' disabled={loading}>
                        {loading ? 'Loading...' : (view === 'login' ? 'Login' : 'Register')}
                    </button>
                </div>
            
                {/* Switch between Login/Register */}
                <div className='register-link'>
                    <p>
                        {view === 'login' ? "Don't have an account?" : "Already have an account?"}{' '}
                        <button 
                            type="button" 
                            className="link-button"
                            onClick={() => {
                                setView(view === 'login' ? 'register' : 'login');
                                setError('');
                                setMessage('');
                                // Clear form fields when switching
                                setUsername('');
                                setEmail('');
                                setPassword('');
                                setFirstName('');
                                setLastName('');
                            }}
                        >
                            {view === 'login' ? 'Register' : 'Login'}
                        </button>
                    </p>
                </div>
            </form>

            {/* "Forget Password?" link positioned outside the form */}
            {view === 'login' && (
                <div className="lost-password-link">
                    <button 
                        type="button" 
                        className="link-button"
                        onClick={() => {
                            // Handle forgot password logic here
                            alert('Forgot password functionality coming soon!');
                        }}
                    >
                        Forget Password?
                    </button>
                </div>
            )}
        </div>
    );
};

export default LoginForm;