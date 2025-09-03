import React, { useState } from 'react';
import './LoginForm.css';

const LoginForm = () => {
    const [view, setView] = useState('login');
    const [username, setUsername] = useState(''); // Changed from email to username
    const [email, setEmail] = useState(''); // Only for registration
    const [password, setPassword] = useState('');
    const [firstName, setFirstName] = useState(''); // For registration
    const [lastName, setLastName] = useState(''); // For registration
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleLogin = async (e) => {
        e.preventDefault();
        setError('');
        setMessage('');
        setLoading(true);
        
        try {
            const response = await fetch(' http://127.0.0.1:8000/api/login/', { // Fixed URL
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password }), // Changed from email to username
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'Login failed. Please check your credentials.');
            }
            
            if (data.success) {
                console.log('Login successful:', data);
                setMessage('Login successful! Welcome.');
                
                // Store tokens in localStorage (optional)
                if (data.tokens) {
                    localStorage.setItem('access_token', data.tokens.access);
                    localStorage.setItem('refresh_token', data.tokens.refresh);
                }
                
                // Store user data
                localStorage.setItem('user', JSON.stringify(data.user));
                
                // Redirect to dashboard or main app (you can customize this)
                // window.location.href = '/dashboard';
            } else {
                throw new Error(data.message || 'Login failed');
            }
        } catch (err) {
            setError(err.message);
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
            const response = await fetch(' http://127.0.0.1:8000/api/register/', { // Fixed URL
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    username, 
                    email, 
                    password,
                    first_name: firstName,
                    last_name: lastName
                }),
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'Registration failed. Please try again.');
            }
            
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
            setError(err.message);
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