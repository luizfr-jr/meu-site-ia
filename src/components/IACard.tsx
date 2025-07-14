import React, { useState } from 'react';
import { Card, CardBody, Image, Button, Tooltip } from '@heroui/react';
import { motion } from 'framer-motion';
import {
  Heart,
  MessageCircle,
  Image as ImageIcon,
  BookOpen,
  Zap,
  Languages,
  Eye,
  Search,
  Code,
  Presentation,
  Sparkles,
  Brain,
  Share2,
  Bookmark,
  Star,
  ExternalLink
} from 'lucide-react';
import type { IAData } from '../types';

interface IACardProps {
  ia: IAData;
}

const categoryIcons = {
  'Conversação': MessageCircle,
  'Geração de Imagens': ImageIcon,
  'Pesquisa Acadêmica': BookOpen,
  'Produtividade': Zap,
  'Tradução': Languages,
  'Visualização': Eye,
  'Busca': Search,
  'Programação': Code,
  'Apresentações': Presentation,
  'Criatividade': Sparkles
};

const categoryColors = {
  'Conversação': 'bg-blue-500 text-white border-blue-500',
  'Geração de Imagens': 'bg-purple-500 text-white border-purple-500',
  'Pesquisa Acadêmica': 'bg-green-500 text-white border-green-500',
  'Produtividade': 'bg-orange-500 text-white border-orange-500',
  'Tradução': 'bg-indigo-500 text-white border-indigo-500',
  'Visualização': 'bg-cyan-500 text-white border-cyan-500',
  'Busca': 'bg-yellow-500 text-white border-yellow-500',
  'Programação': 'bg-gray-500 text-white border-gray-500',
  'Apresentações': 'bg-rose-500 text-white border-rose-500',
  'Criatividade': 'bg-pink-500 text-white border-pink-500'
};

const IACard: React.FC<IACardProps> = ({ ia }) => {
  const [isLiked, setIsLiked] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [imageError, setImageError] = useState(false);

  const handleImageError = () => {
    setImageError(true);
  };

  const toggleLike = () => {
    setIsLiked(!isLiked);
  };

  const toggleSave = () => {
    setIsSaved(!isSaved);
  };

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: ia.name,
          text: ia.description,
          url: ia.url,
        });
      } catch (error) {
        console.log('Error sharing:', error);
      }
    } else {
      navigator.clipboard.writeText(ia.url);
    }
  };

  const IconComponent = categoryIcons[ia.category as keyof typeof categoryIcons] || Brain;
  const categoryColor = categoryColors[ia.category as keyof typeof categoryColors] || 'bg-blue-500 text-white border-blue-500';

  // Simulando rating (4.0 a 5.0) e reviews
  const rating = (4 + Math.random()).toFixed(1);
  const reviews = Math.floor(Math.random() * 2000) + 500;

  return (
    <motion.div
      className="group relative w-full max-w-sm mx-auto h-[420px]"
      whileHover={{ y: -8, scale: 1.02 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
    >
      <Card className="h-full bg-white/60 dark:bg-gray-800/60 backdrop-blur-xl border border-gray-200/50 dark:border-gray-700/50 overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300">
        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent dark:from-gray-800/20 pointer-events-none" />

        {/* Quick Actions - Appear on Hover */}
        <motion.div
          className="absolute top-4 right-4 flex space-x-2 opacity-0 group-hover:opacity-100 z-10 transition-opacity duration-200"
        >
          <Tooltip content="Curtir">
            <motion.button
              onClick={toggleLike}
              className={`p-2 rounded-lg backdrop-blur-sm border border-white/20 transition-all duration-200 ${
                isLiked ? "bg-red-500/20 text-red-500" : "bg-white/20 text-gray-600 dark:text-gray-300 hover:bg-white/30"
              }`}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
            >
              <Heart className={`w-4 h-4 ${isLiked ? "fill-current" : ""}`} />
            </motion.button>
          </Tooltip>

          <Tooltip content="Salvar">
            <motion.button
              onClick={toggleSave}
              className={`p-2 rounded-lg backdrop-blur-sm border border-white/20 transition-all duration-200 ${
                isSaved ? "bg-blue-500/20 text-blue-500" : "bg-white/20 text-gray-600 dark:text-gray-300 hover:bg-white/30"
              }`}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
            >
              <Bookmark className={`w-4 h-4 ${isSaved ? "fill-current" : ""}`} />
            </motion.button>
          </Tooltip>

          <Tooltip content="Compartilhar">
            <motion.button
              onClick={handleShare}
              className="p-2 rounded-lg backdrop-blur-sm border border-white/20 bg-white/20 text-gray-600 dark:text-gray-300 hover:bg-white/30 transition-all duration-200"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
            >
              <Share2 className="w-4 h-4" />
            </motion.button>
          </Tooltip>
        </motion.div>

        {/* Tool Image/Logo Section */}
        <div className="relative h-32 bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800 flex items-center justify-center">
          {!imageError ? (
            <Image
              src={ia.image}
              alt={ia.name}
              width={64}
              height={64}
              className="object-contain"
              onError={handleImageError}
            />
          ) : (
            <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center">
              <IconComponent className="w-8 h-8 text-white" />
            </div>
          )}

          {/* Category Badge */}
          <div className={`absolute top-4 left-4 px-3 py-1 rounded-full text-xs font-medium flex items-center space-x-1 ${categoryColor}`}>
            <IconComponent className="w-3 h-3" />
            <span>{ia.category}</span>
          </div>
        </div>

        {/* Content */}
        <CardBody className="p-5 flex flex-col h-72">
          {/* Title */}
          <h3 className="text-lg font-bold text-gray-900 dark:text-white line-clamp-1 mb-2">{ia.name}</h3>

          {/* Description */}
          <p className="text-sm text-gray-600 dark:text-gray-300 line-clamp-3 leading-relaxed mb-3 flex-shrink-0">
            {ia.description}
          </p>

          {/* Tags */}
          <div className="flex flex-wrap gap-2 mb-3 flex-shrink-0">
            {ia.tags.slice(0, 3).map((tag, index) => (
              <span
                key={index}
                className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded-md"
              >
                {tag}
              </span>
            ))}
          </div>

          {/* Rating */}
          <div className="flex items-center space-x-1 mb-4 flex-shrink-0">
            <Star className="w-4 h-4 text-yellow-400 fill-current" />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{rating}</span>
            <span className="text-xs text-gray-500 dark:text-gray-400">({reviews} avaliações)</span>
          </div>

          {/* Spacer to push button to bottom */}
          <div className="flex-1"></div>

          {/* CTA Button - Fixed at bottom */}
          <motion.div
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Button
              as="a"
              href={ia.url}
              target="_blank"
              rel="noopener noreferrer"
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium shadow-lg hover:shadow-xl"
              endContent={<ExternalLink className="w-4 h-4" />}
            >
              Acessar Ferramenta
            </Button>
          </motion.div>
        </CardBody>
      </Card>
    </motion.div>
  );
};

export default IACard;