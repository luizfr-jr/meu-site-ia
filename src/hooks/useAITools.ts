import { useState, useEffect, useCallback } from 'react';
import { DatabaseService } from '../services/database';
import { initialIAs } from '../data/ias';
import type { IAData } from '../types';

interface UseAIToolsReturn {
  tools: IAData[];
  loading: boolean;
  error: string | null;
  addTool: (toolData: Omit<IAData, 'id' | 'createdAt' | 'updatedAt'>) => Promise<void>;
  updateTool: (id: string, toolData: Partial<Omit<IAData, 'id' | 'createdAt'>>) => Promise<void>;
  deleteTool: (id: string) => Promise<void>;
  refreshTools: () => Promise<void>;
  isDatabaseMode: boolean;
}

export const useAITools = (): UseAIToolsReturn => {
  const [tools, setTools] = useState<IAData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDatabaseMode, setIsDatabaseMode] = useState(false);

  // Check if database is available and set up accordingly
  const initializeTools = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      if (DatabaseService.isDatabaseAvailable()) {
        setIsDatabaseMode(true);
        
        // Try to initialize with default data if database is empty
        await DatabaseService.initializeWithDefaultData(initialIAs);
        
        // Set up real-time subscription
        const unsubscribe = DatabaseService.subscribeToTools((updatedTools) => {
          setTools(updatedTools);
          setLoading(false);
          setError(null);
        });
        
        return unsubscribe;
      } else {
        // Use static data when database is not configured
        setIsDatabaseMode(false);
        setTools(initialIAs);
        setLoading(false);
        setError('Usando dados locais - banco de dados não configurado');
        
        return () => {}; // No-op unsubscribe
      }
    } catch (err) {
      console.error('Failed to initialize tools:', err);
      // Fall back to static data on any error
      setIsDatabaseMode(false);
      setTools(initialIAs);
      setError('Erro ao conectar com banco de dados - usando dados locais');
      setLoading(false);
      
      return () => {}; // No-op unsubscribe
    }
  }, []);

  // Initialize on mount
  useEffect(() => {
    let unsubscribe: (() => void) | null = null;

    initializeTools().then((unsub) => {
      unsubscribe = unsub;
    });

    return () => {
      if (unsubscribe) {
        unsubscribe();
      }
    };
  }, [initializeTools]);

  // Add new tool
  const addTool = useCallback(async (toolData: Omit<IAData, 'id' | 'createdAt' | 'updatedAt'>) => {
    if (!isDatabaseMode) {
      throw new Error('Banco de dados não configurado - não é possível adicionar ferramentas');
    }
    
    try {
      setError(null);
      await DatabaseService.addTool(toolData);
      // Real-time subscription will update the state automatically
    } catch (err) {
      console.error('Failed to add tool:', err);
      setError('Falha ao adicionar ferramenta');
      throw err;
    }
  }, [isDatabaseMode]);

  // Update existing tool
  const updateTool = useCallback(async (id: string, toolData: Partial<Omit<IAData, 'id' | 'createdAt'>>) => {
    if (!isDatabaseMode) {
      throw new Error('Banco de dados não configurado - não é possível atualizar ferramentas');
    }
    
    try {
      setError(null);
      await DatabaseService.updateTool(id, toolData);
      // Real-time subscription will update the state automatically
    } catch (err) {
      console.error('Failed to update tool:', err);
      setError('Falha ao atualizar ferramenta');
      throw err;
    }
  }, [isDatabaseMode]);

  // Delete tool
  const deleteTool = useCallback(async (id: string) => {
    if (!isDatabaseMode) {
      throw new Error('Banco de dados não configurado - não é possível excluir ferramentas');
    }
    
    try {
      setError(null);
      await DatabaseService.deleteTool(id);
      // Real-time subscription will update the state automatically
    } catch (err) {
      console.error('Failed to delete tool:', err);
      setError('Falha ao excluir ferramenta');
      throw err;
    }
  }, [isDatabaseMode]);

  // Manual refresh (only works in database mode)
  const refreshTools = useCallback(async () => {
    if (!isDatabaseMode) {
      setTools(initialIAs);
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      const toolsFromDB = await DatabaseService.getAllTools();
      setTools(toolsFromDB);
    } catch (err) {
      console.error('Failed to refresh tools:', err);
      setError('Falha ao atualizar ferramentas');
    } finally {
      setLoading(false);
    }
  }, [isDatabaseMode]);

  return {
    tools,
    loading,
    error,
    addTool,
    updateTool,
    deleteTool,
    refreshTools,
    isDatabaseMode
  };
};