import { create } from 'zustand';
import { authService } from '@/services/auth.service';

interface User {
  id: string;
  email: string;
  role: string;
  full_name?: string;
  hv_id?: string;
}

interface AuthState {
  user: User | null;
  isLoading: boolean;
  pendingUserId: string | null;
  pendingRole: string | null;
  setUser: (user: User | null) => void;
  setPending: (userId: string, role: string) => void;
  clearPending: () => void;
  logout: () => Promise<void>;
  loadUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  pendingUserId: null,
  pendingRole: null,

  setUser: (user) => set({ user, isLoading: false }),
  setPending: (userId, role) => set({ pendingUserId: userId, pendingRole: role }),
  clearPending: () => set({ pendingUserId: null, pendingRole: null }),

  logout: async () => {
    await authService.logout();
    set({ user: null, isLoading: false });
  },

  loadUser: async () => {
    try {
      const user = await authService.getStoredUser();
      set({ user, isLoading: false });
    } catch {
      set({ user: null, isLoading: false });
    }
  },
}));
