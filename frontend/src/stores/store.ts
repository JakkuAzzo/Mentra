import { create } from 'zustand';

interface User {
  id: number;
  email: string;
  username: string;
  full_name: string;
  learning_style: string;
}

interface AuthStore {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  setUser: (user: User) => void;
  setToken: (token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  token: localStorage.getItem('access_token'),
  isAuthenticated: !!localStorage.getItem('access_token'),
  setUser: (user) => set({ user, isAuthenticated: true }),
  setToken: (token) => {
    localStorage.setItem('access_token', token);
    set({ token, isAuthenticated: true });
  },
  logout: () => {
    localStorage.removeItem('access_token');
    set({ user: null, token: null, isAuthenticated: false });
  },
}));

interface LearningStore {
  currentTopic: any | null;
  currentQuestion: any | null;
  progress: any | null;
  setCurrentTopic: (topic: any) => void;
  setCurrentQuestion: (question: any) => void;
  setProgress: (progress: any) => void;
}

export const useLearningStore = create<LearningStore>((set) => ({
  currentTopic: null,
  currentQuestion: null,
  progress: null,
  setCurrentTopic: (topic) => set({ currentTopic: topic }),
  setCurrentQuestion: (question) => set({ currentQuestion: question }),
  setProgress: (progress) => set({ progress }),
}));
