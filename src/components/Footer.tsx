import React from 'react';
import { Link } from 'react-router-dom';
import { Github, Settings, Heart } from 'lucide-react';

const Footer: React.FC = () => {
  return (
    <footer className="bg-gradient-to-r from-slate-800 to-slate-900 dark:from-slate-900 dark:to-black text-white py-12 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center space-y-6">
          {/* Informações dos desenvolvedores */}
          <div className="text-center space-y-3">
            <h3 className="text-lg font-semibold text-blue-300">Desenvolvido por</h3>
            <div className="space-y-2">
              <p className="text-sm font-medium">Dr. Luiz Fernando Rodrigues Jr.</p>
              <p className="text-sm font-medium">Kalleby Evangelho Mota</p>
            </div>
          </div>

          {/* GitHub e Admin */}
          <div className="flex items-center space-x-6">
            <a
              href="https://github.com/luizfr-jr/meu-site-ia"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-2 hover:text-blue-300 transition-colors duration-300 text-sm"
            >
              <Github className="w-5 h-5" />
              <span>GitHub</span>
            </a>
            <Link
              to="/admin"
              className="flex items-center space-x-2 hover:text-blue-300 transition-colors duration-300 text-sm"
            >
              <Settings className="w-5 h-5" />
              <span>Admin</span>
            </Link>
          </div>
          
          {/* Mensagem com coração */}
          <div className="text-center space-y-2">
            <p className="text-sm flex items-center justify-center space-x-2">
              <span>Desenvolvido com</span>
              <Heart className="w-4 h-4 text-red-500 fill-current" />
              <span>para a comunidade científica</span>
            </p>
            <p className="text-xs opacity-80">
              © 2025 Hub Científico. Todos os direitos reservados.
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;