import React, { createContext, useState, useEffect, useContext } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check login status on mount
  useEffect(() => {
    const initializeAuth = async () => {
      const token = localStorage.getItem('access_token');
      const storedUser = localStorage.getItem('user');
      
      if (token && storedUser) {
        try {
          // Verify token validity by calling profile endpoint
          const res = await api.get('/users/me');
          setUser(res.data);
          setIsAuthenticated(true);
          localStorage.setItem('user', JSON.stringify(res.data));
        } catch (err) {
          console.error("Session verification failed:", err);
          // Token is invalid/expired and refresh failed in interceptor
          logout();
        }
      }
      setLoading(false);
    };

    initializeAuth();
  }, []);

  const login = async (username, password) => {
    setLoading(true);
    setError(null);
    try {
      // FastAPI OAuth2PasswordRequestForm expects form-urlencoded body
      const params = new URLSearchParams();
      params.append('username', username);
      params.append('password', password);

      const response = await api.post('/auth/login', params, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });

      const { access_token, refresh_token } = response.data;
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);

      // Retrieve user details with the newly acquired token
      const profileResponse = await api.get('/users/me');
      setUser(profileResponse.data);
      setIsAuthenticated(true);
      localStorage.setItem('user', JSON.stringify(profileResponse.data));
      setLoading(false);
      return profileResponse.data;
    } catch (err) {
      console.error("Login failed:", err);
      const errMsg = err.response?.data?.detail || "Invalid username or password";
      setError(errMsg);
      setLoading(false);
      throw new Error(errMsg);
    }
  };

  const register = async (username, email, password, role_id) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post('/auth/register', {
        username,
        email,
        password,
        role_id: parseInt(role_id)
      });
      setLoading(false);
      return response.data;
    } catch (err) {
      console.error("Registration failed:", err);
      const errMsg = err.response?.data?.detail || "Registration failed. Try again.";
      setError(errMsg);
      setLoading(false);
      throw new Error(errMsg);
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setUser(null);
    setIsAuthenticated(false);
    setError(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        loading,
        error,
        login,
        register,
        logout,
        setError
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
