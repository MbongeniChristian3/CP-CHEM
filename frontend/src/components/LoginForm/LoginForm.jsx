import React, { useState } from 'react';
import './LoginForm.css';


const LoginForm = () => {
    const [view, setView] = useState('login');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleLogin = async (e) => {
        e.preventDefault();
        setError('');
        setMessage('');
        setLoading(true);
        
        try {
            const response = await fetch('http://127.0.0.1:8000/api/auth/login/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Login failed. Please check your credentials.');
            }
            
            const data = await response.json();
            console.log('Login successful:', data);
            setMessage('Login successful! Welcome.');
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
            const response = await fetch('http://127.0.0.1:8000/api/auth/register/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                const errorMessage = Object.values(errorData).flat().join(' ');
                throw new Error(errorMessage || 'Registration failed. Please try again.');
            }
            
            const data = await response.json();
            console.log('Registration successful:', data);
            setMessage('Registration successful! Please log in.');
            setView('login');
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

                {/* Username/Email Input Group */}
                <div className='form-group'>
                    <label htmlFor="email">Username</label>
                    <div className='input-box'>
                        <input
                            type="text"
                            id="email"
                            required
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="Enter your username"
                        />
                    </div>
                </div>

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
                    <label>
                        <input type="checkbox"/>
                        Remember me
                    </label>
                    <button type='submit' className='btn' disabled={loading}>
                        {loading ? 'Loading...' : (view === 'login' ? 'Login' : 'Register')}
                    </button>
                </div>
            
                {/* Don't have an account? Register link */}
                <div className='register-link'>
                    <p>
                        {view === 'login' ? "Don't have an account?" : "Already have an account?"}{' '}
                        <a href="#" onClick={(e) => {
                            e.preventDefault();
                            setView(view === 'login' ? 'register' : 'login');
                            setError('');
                            setMessage('');
                        }}>
                            {view === 'login' ? 'Register' : 'Login'}
                        </a>
                    </p>
                </div>
            </form>

            {/* "Forget Password?" link positioned outside the form */}
            {view === 'login' && (
                <div className="lost-password-link">
                    <a href="#" onClick={(e) => e.preventDefault()}>Forget Password?</a>
                </div>
            )}
        </div>
    );
};

export default LoginForm