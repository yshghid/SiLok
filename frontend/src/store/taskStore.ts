import { create } from 'zustand';
import { Task, TaskFilter, DateRange } from '../types';
import api from '../services/api';
import { format, startOfWeek, endOfWeek } from 'date-fns';

interface TaskState {
  tasks: Task[];
  filteredTasks: Task[];
  isLoading: boolean;
  error: string | null;
  dateRange: DateRange;
  filter: TaskFilter;
  selectedTasks: number[];
  setDateRange: (range: DateRange) => void;
  setFilter: (filter: TaskFilter) => void;
  fetchTasks: (email: string) => Promise<void>;
  selectTask: (taskId: number) => void;
  deselectTask: (taskId: number) => void;
  selectAllTasks: () => void;
  clearSelection: () => void;
  clearError: () => void;
}

const getDefaultDateRange = (): DateRange => {
  const today = new Date();
  return {
    start: startOfWeek(today, { weekStartsOn: 1 }),
    end: endOfWeek(today, { weekStartsOn: 1 }),
  };
};

export const useTaskStore = create<TaskState>((set, get) => ({
  tasks: [],
  filteredTasks: [],
  isLoading: false,
  error: null,
  dateRange: getDefaultDateRange(),
  filter: {},
  selectedTasks: [],

  setDateRange: (range: DateRange) => {
    set({ dateRange: range });
  },

  setFilter: (filter: TaskFilter) => {
    set({ filter });
    const { tasks } = get();
    const filteredTasks = applyFilters(tasks, filter);
    set({ filteredTasks });
  },

  fetchTasks: async (email: string) => {
    const { dateRange, filter } = get();
    set({ isLoading: true, error: null });

    try {
      const startDate = format(dateRange.start, 'yyyy-MM-dd');
      const endDate = format(dateRange.end, 'yyyy-MM-dd');

      const tasks = await api.getUserTimeline(email, startDate, endDate);
      const filteredTasks = applyFilters(tasks, filter);

      set({ tasks, filteredTasks, isLoading: false });
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : '업무 목록을 불러오는데 실패했습니다.';
      set({ error: message, isLoading: false });
    }
  },

  selectTask: (taskId: number) => {
    set((state) => ({
      selectedTasks: [...state.selectedTasks, taskId],
    }));
  },

  deselectTask: (taskId: number) => {
    set((state) => ({
      selectedTasks: state.selectedTasks.filter((id) => id !== taskId),
    }));
  },

  selectAllTasks: () => {
    const { filteredTasks } = get();
    set({ selectedTasks: filteredTasks.map((t) => t.task_id) });
  },

  clearSelection: () => {
    set({ selectedTasks: [] });
  },

  clearError: () => {
    set({ error: null });
  },
}));

// Helper function to apply filters
function applyFilters(tasks: Task[], filter: TaskFilter): Task[] {
  let result = [...tasks];

  if (filter.platform) {
    result = result.filter((t) => t.platform === filter.platform);
  }

  if (filter.search) {
    const searchLower = filter.search.toLowerCase();
    result = result.filter(
      (t) =>
        t.content.toLowerCase().includes(searchLower) ||
        t.sender.toLowerCase().includes(searchLower) ||
        t.receiver.toLowerCase().includes(searchLower)
    );
  }

  return result;
}
