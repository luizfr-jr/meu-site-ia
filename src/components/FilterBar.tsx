import React from 'react';
import { Chip, Button } from '@heroui/react';
import { Filter, X, Sparkles } from 'lucide-react';
import { categories } from '../data/ias';

interface FilterBarProps {
  selectedCategory: string;
  onCategoryChange: (category: string) => void;
}

const FilterBar: React.FC<FilterBarProps> = ({ selectedCategory, onCategoryChange }) => {
  return (
    <div className="glass-effect border-b border-gray-200/50 dark:border-gray-700/50 py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-6">
          {/* Header */}
          <div className="flex items-center gap-3 text-gray-700 dark:text-gray-200">
            <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg">
              <Filter className="w-4 h-4 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-semibold gradient-text">Explorar Categorias</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">Descubra ferramentas por área de interesse</p>
            </div>
          </div>
          
          {/* Filter Chips */}
          <div className="flex flex-wrap gap-3">
            <Chip
              onClick={() => onCategoryChange('all')}
              className={`cursor-pointer transition-all duration-300 transform hover:scale-105 ${
                selectedCategory === 'all'
                  ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg'
                  : 'bg-white/80 dark:bg-gray-800/80 text-gray-700 dark:text-gray-200 hover:bg-white dark:hover:bg-gray-700'
              }`}
              startContent={selectedCategory === 'all' ? <Sparkles className="w-3 h-3" /> : null}
            >
              Todas as Categorias
            </Chip>
            
            {categories.map((category, index) => (
              <Chip
                key={category}
                onClick={() => onCategoryChange(category)}
                className={`cursor-pointer transition-all duration-300 transform hover:scale-105 animate-fade-in ${
                  selectedCategory === category
                    ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg'
                    : 'bg-white/80 dark:bg-gray-800/80 text-gray-700 dark:text-gray-200 hover:bg-white dark:hover:bg-gray-700'
                }`}
                style={{ animationDelay: `${index * 50}ms` }}
              >
                {category}
              </Chip>
            ))}
          </div>
          
          {/* Active Filter Display */}
          {selectedCategory && selectedCategory !== 'all' && (
            <div className="flex items-center gap-3 animate-fade-in">
              <span className="text-sm text-gray-600 dark:text-gray-400 font-medium">Filtro ativo:</span>
              <Chip
                className="bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-700"
                endContent={
                  <Button
                    isIconOnly
                    size="sm"
                    variant="light"
                    onClick={() => onCategoryChange('all')}
                    className="min-w-unit-6 w-6 h-6 text-blue-600 dark:text-blue-400 hover:bg-blue-200 dark:hover:bg-blue-800/50"
                  >
                    <X className="w-3 h-3" />
                  </Button>
                }
              >
                {selectedCategory}
              </Chip>
              <span className="text-xs text-gray-500 dark:text-gray-400">
                Clique no × para remover
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FilterBar;