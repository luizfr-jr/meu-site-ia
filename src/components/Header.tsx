import React, { useState, useEffect } from 'react';
import { Navbar, NavbarBrand, NavbarContent, NavbarItem, Button, Input } from '@heroui/react';
import { Search, Brain, Moon, Sun } from 'lucide-react';

interface HeaderProps {
  searchTerm: string;
  onSearchChange: (value: string) => void;
}

const Header: React.FC<HeaderProps> = ({ searchTerm, onSearchChange }) => {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    // Verificar preferência salva ou do sistema
    const savedTheme = localStorage.getItem('theme');
    const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme === 'dark' || (!savedTheme && systemDark)) {
      setIsDark(true);
      document.documentElement.classList.add('dark');
    } else {
      setIsDark(false);
      document.documentElement.classList.remove('dark');
    }
  }, []);

  const toggleTheme = () => {
    const newTheme = !isDark;
    setIsDark(newTheme);
    
    if (newTheme) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  };

  return (
    <header className="sticky top-0 z-50 glass-effect border-b border-white/10">
      <Navbar className="bg-transparent backdrop-blur-md">
        <NavbarBrand className="flex items-center gap-3 animate-slide-in">
          <div className="relative">
            <Brain className="w-8 h-8 text-blue-500 animate-pulse" />
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full animate-bounce"></div>
          </div>
          <div>
            <h1 className="text-xl font-bold gradient-text">Hub Científico</h1>
            <p className="text-sm text-gray-600 dark:text-gray-300">Ferramentas de IA para Estudos</p>
          </div>
        </NavbarBrand>
        
        <NavbarContent className="hidden sm:flex gap-4" justify="center">
          <NavbarItem className="flex-1 max-w-md">
            <div className="relative w-full">
              <Input
                placeholder="Buscar ferramentas..."
                value={searchTerm}
                onChange={(e) => onSearchChange(e.target.value)}
                startContent={<Search className="w-4 h-4 text-gray-400" />}
                className="w-full search-bar"
                classNames={{
                  input: "bg-transparent text-gray-900 dark:text-gray-100 placeholder:text-gray-500 dark:placeholder:text-gray-400",
                  inputWrapper: "bg-white/50 dark:bg-gray-800/50 border-gray-200 dark:border-gray-700 hover:bg-white/70 dark:hover:bg-gray-800/70 transition-all duration-300"
                }}
              />
            </div>
          </NavbarItem>
        </NavbarContent>
        
        <NavbarContent justify="end">
          <NavbarItem>
            <Button
              isIconOnly
              variant="light"
              className="text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-300"
              onClick={toggleTheme}
            >
              {isDark ?
                <Sun className="w-5 h-5" /> :
                <Moon className="w-5 h-5" />
              }
            </Button>
          </NavbarItem>
          
          <NavbarItem className="sm:hidden">
            <Button
              isIconOnly
              variant="light"
              className="text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-300"
            >
              <Search className="w-5 h-5" />
            </Button>
          </NavbarItem>
        </NavbarContent>
      </Navbar>
    </header>
  );
};

export default Header;