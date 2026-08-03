import { create } from "zustand";

interface UIState {
  isCmdkOpen: boolean;
  isEvidenceRailOpen: boolean;
  openCmdk: () => void;
  closeCmdk: () => void;
  toggleCmdk: () => void;
  toggleEvidenceRail: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  isCmdkOpen: false,
  isEvidenceRailOpen: true,
  openCmdk: () => set({ isCmdkOpen: true }),
  closeCmdk: () => set({ isCmdkOpen: false }),
  toggleCmdk: () => set((state) => ({ isCmdkOpen: !state.isCmdkOpen })),
  toggleEvidenceRail: () => set((state) => ({ isEvidenceRailOpen: !state.isEvidenceRailOpen })),
}));
