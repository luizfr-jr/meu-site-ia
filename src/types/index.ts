export interface IAData {
  id: string;
  name: string;
  description: string;
  image: string;
  url: string;
  category: string;
  tags: string[];
  createdAt: Date;
  updatedAt: Date;
}

export interface User {
  id: string;
  email: string;
  isAdmin: boolean;
  name?: string;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface AuthContextType {
  user: User | null;
  login: (data: LoginData) => Promise<boolean>;
  logout: () => void;
  isAuthenticated: boolean;
  isAdmin: boolean;
}