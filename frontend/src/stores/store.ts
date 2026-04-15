import { create } from 'zustand';

interface User {
  id: number;
  email: string;
  username: string;
  full_name: string;
  learning_style: string;
  role?: string;
  access_level?: number;
}

function decodeJwtPayload(token: string): { sub?: string; email?: string } | null {
  try {
    const payload = token.split('.')[1];
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
    const decoded = atob(base64.padEnd(base64.length + (4 - (base64.length % 4 || 4)) % 4, '='));
    return JSON.parse(decoded);
  } catch {
    return null;
  }
}

function buildUserFromToken(token: string): User | null {
  const payload = decodeJwtPayload(token);
  if (!payload?.sub || !payload?.email) {
    return null;
  }

  const fallbackName = payload.email.split('@')[0] || 'student';
  return {
    id: Number(payload.sub),
    email: payload.email,
    username: fallbackName,
    full_name: fallbackName,
    learning_style: 'adaptive',
    role: 'student',
    access_level: 1,
  };
}

const initialToken = localStorage.getItem('access_token');
const initialUser = initialToken ? buildUserFromToken(initialToken) : null;

interface AuthStore {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  setUser: (user: User) => void;
  setToken: (token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: initialUser,
  token: initialToken,
  isAuthenticated: !!initialToken,
  setUser: (user) => set({ user, isAuthenticated: true }),
  setToken: (token) => {
    localStorage.setItem('access_token', token);
    set({ token, user: buildUserFromToken(token), isAuthenticated: true });
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
