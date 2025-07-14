import {
  collection,
  doc,
  getDocs,
  addDoc,
  updateDoc,
  deleteDoc,
  query,
  orderBy,
  Timestamp,
  onSnapshot,
  type Unsubscribe
} from 'firebase/firestore';
import { db, isFirebaseConfigured } from './firebase';
import type { IAData } from '../types';

const COLLECTION_NAME = 'ai-tools';

// Convert Firestore Timestamp to Date
const convertTimestamps = (data: any): IAData => ({
  ...data,
  createdAt: data.createdAt?.toDate() || new Date(),
  updatedAt: data.updatedAt?.toDate() || new Date()
});

// Convert Date to Firestore Timestamp  
const convertToFirestore = (data: Partial<IAData>) => ({
  ...data,
  createdAt: data.createdAt ? Timestamp.fromDate(data.createdAt) : Timestamp.now(),
  updatedAt: Timestamp.now()
});

export class DatabaseService {
  // Check if database is available
  static isDatabaseAvailable(): boolean {
    return isFirebaseConfigured();
  }

  // Get all AI tools
  static async getAllTools(): Promise<IAData[]> {
    if (!this.isDatabaseAvailable()) {
      throw new Error('Database not configured - falling back to static data');
    }
    
    try {
      const q = query(collection(db, COLLECTION_NAME), orderBy('createdAt', 'desc'));
      const querySnapshot = await getDocs(q);
      return querySnapshot.docs.map(doc => ({
        ...convertTimestamps(doc.data()),
        id: doc.id
      }));
    } catch (error) {
      console.error('Error fetching tools:', error);
      throw new Error('Failed to fetch AI tools');
    }
  }

  // Real-time subscription to AI tools
  static subscribeToTools(callback: (tools: IAData[]) => void): Unsubscribe {
    if (!this.isDatabaseAvailable()) {
      // Return a no-op unsubscribe function for non-configured Firebase
      setTimeout(() => callback([]), 0);
      return () => {};
    }

    const q = query(collection(db, COLLECTION_NAME), orderBy('createdAt', 'desc'));
    
    return onSnapshot(q, (querySnapshot) => {
      const tools = querySnapshot.docs.map(doc => ({
        ...convertTimestamps(doc.data()),
        id: doc.id
      }));
      callback(tools);
    }, (error) => {
      console.error('Error in tools subscription:', error);
      // Fallback to empty array on error
      callback([]);
    });
  }

  // Add new AI tool
  static async addTool(toolData: Omit<IAData, 'id' | 'createdAt' | 'updatedAt'>): Promise<string> {
    if (!this.isDatabaseAvailable()) {
      throw new Error('Database not configured - cannot add tools');
    }
    
    try {
      const firestoreData = convertToFirestore({
        ...toolData,
        createdAt: new Date(),
        updatedAt: new Date()
      });
      
      const docRef = await addDoc(collection(db, COLLECTION_NAME), firestoreData);
      return docRef.id;
    } catch (error) {
      console.error('Error adding tool:', error);
      throw new Error('Failed to add AI tool');
    }
  }

  // Update existing AI tool
  static async updateTool(id: string, toolData: Partial<Omit<IAData, 'id' | 'createdAt'>>): Promise<void> {
    if (!this.isDatabaseAvailable()) {
      throw new Error('Database not configured - cannot update tools');
    }
    
    try {
      const docRef = doc(db, COLLECTION_NAME, id);
      const firestoreData = convertToFirestore({
        ...toolData,
        updatedAt: new Date()
      });
      
      await updateDoc(docRef, firestoreData);
    } catch (error) {
      console.error('Error updating tool:', error);
      throw new Error('Failed to update AI tool');
    }
  }

  // Delete AI tool
  static async deleteTool(id: string): Promise<void> {
    if (!this.isDatabaseAvailable()) {
      throw new Error('Database not configured - cannot delete tools');
    }
    
    try {
      const docRef = doc(db, COLLECTION_NAME, id);
      await deleteDoc(docRef);
    } catch (error) {
      console.error('Error deleting tool:', error);
      throw new Error('Failed to delete AI tool');
    }
  }

  // Initialize database with initial data (for first time setup)
  static async initializeWithDefaultData(tools: IAData[]): Promise<void> {
    if (!this.isDatabaseAvailable()) {
      console.log('Database not configured, skipping initialization');
      return;
    }
    
    try {
      // Check if collection is empty
      const existingTools = await this.getAllTools();
      if (existingTools.length > 0) {
        console.log('Database already has data, skipping initialization');
        return;
      }

      console.log('Initializing database with default data...');
      
      // Add all tools to database
      const promises = tools.map(tool => 
        this.addTool({
          name: tool.name,
          description: tool.description,
          image: tool.image,
          url: tool.url,
          category: tool.category,
          tags: tool.tags
        })
      );

      await Promise.all(promises);
      console.log('Database initialized successfully');
    } catch (error) {
      console.error('Error initializing database:', error);
      throw new Error('Failed to initialize database');
    }
  }
}