import React, { useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import Cookies from 'js-cookie';
import type { User, LoginData, AuthContextType } from '../types';
import { AuthContext } from './auth-context';

interface AuthProviderProps {
  children: ReactNode;
}

// Usuários admin autorizados
const ADMIN_USERS = [
  {
    id: '1',
    email: import.meta.env.VITE_ADMIN_USER_1_EMAIL,
    password: import.meta.env.VITE_ADMIN_USER_1_PASSWORD,
    isAdmin: true,
    name: 'Kalleby'
  },
  {
    id: '2',
    email: import.meta.env.VITE_ADMIN_USER_2_EMAIL,
    password: import.meta.env.VITE_ADMIN_USER_2_PASSWORD,
    isAdmin: true,
    name: 'Luiz'
  }
];

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Verificar se há um token salvo
    const token = Cookies.get('auth_token');
    if (token) {
      try {
        const userData = JSON.parse(atob(token));
        setUser(userData);
      } catch (error) {
        console.error('Erro ao decodificar token:', error);
        Cookies.remove('auth_token');
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (data: LoginData): Promise<boolean> => {
    try {
      // Encontrar usuário admin válido
      const adminUser = ADMIN_USERS.find(
        user => user.email === data.email && user.password === data.password
      );
      
      if (adminUser) {
        // Criar objeto de usuário sem senha para o token
        const userForToken = {
          id: adminUser.id,
          email: adminUser.email,
          isAdmin: adminUser.isAdmin,
          name: adminUser.name
        };
        
        const token = btoa(JSON.stringify(userForToken));
        Cookies.set('auth_token', token, { expires: 7 }); // Expira em 7 dias
        setUser(userForToken);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Erro no login:', error);
      return false;
    }
  };

  const logout = () => {
    Cookies.remove('auth_token');
    setUser(null);
  };

  const value: AuthContextType = {
    user,
    login,
    logout,
    isAuthenticated: !!user,
    isAdmin: user?.isAdmin || false,
  };

  if (isLoading) {
    return <div className="flex items-center justify-center min-h-screen">Carregando...</div>;
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};