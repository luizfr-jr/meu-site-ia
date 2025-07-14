import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardBody, CardHeader, Input, Button, Divider } from '@heroui/react';
import { Lock, User, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isVisible, setIsVisible] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const success = await login({ email, password });
      if (success) {
        navigate('/admin');
      } else {
        setError('Credenciais inválidas. Tente novamente.');
      }
    } catch {
      setError('Erro ao fazer login. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  const toggleVisibility = () => setIsVisible(!isVisible);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="flex flex-col items-center space-y-2 pb-6">
          <div className="p-3 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full">
            <Lock className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Área do Administrador</h1>
          <p className="text-gray-600 text-center">
            Faça login para gerenciar as ferramentas de IA
          </p>
        </CardHeader>
        
        <Divider />
        
        <CardBody className="space-y-6 pt-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              type="email"
              label="Email"
              placeholder="Digite seu email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              startContent={<User className="w-4 h-4 text-gray-400" />}
              required
              variant="bordered"
            />
            
            <Input
              label="Senha"
              placeholder="Digite sua senha"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              startContent={<Lock className="w-4 h-4 text-gray-400" />}
              endContent={
                <button
                  className="focus:outline-none"
                  type="button"
                  onClick={toggleVisibility}
                >
                  {isVisible ? (
                    <EyeOff className="w-4 h-4 text-gray-400" />
                  ) : (
                    <Eye className="w-4 h-4 text-gray-400" />
                  )}
                </button>
              }
              type={isVisible ? "text" : "password"}
              required
              variant="bordered"
            />
            
            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}
            
            <Button
              type="submit"
              color="primary"
              className="w-full"
              size="lg"
              isLoading={loading}
              disabled={loading}
            >
              {loading ? 'Entrando...' : 'Entrar'}
            </Button>
          </form>
          
          <div className="text-center pt-4">
            <p className="text-sm text-gray-600">
              Apenas administradores autorizados podem acessar esta área.
            </p>
          </div>
        </CardBody>
      </Card>
    </div>
  );
};

export default LoginPage;