import { create } from 'zustand';
import { Report, Task } from '../types';
import api from '../services/api';

interface GenerateReportParams {
  tasks: Task[];
  startDate: string;
  endDate: string;
  writer: string;
  email: string;
}

interface ReportState {
  reports: Report[];
  currentReport: Report | null;
  generatedContent: string | null;
  isLoading: boolean;
  isGenerating: boolean;
  error: string | null;
  fetchReports: (userId: number) => Promise<void>;
  fetchReport: (reportId: number) => Promise<void>;
  generateReport: (params: GenerateReportParams) => Promise<void>;
  setCurrentReport: (report: Report | null) => void;
  clearGeneratedContent: () => void;
  clearError: () => void;
}

export const useReportStore = create<ReportState>((set) => ({
  reports: [],
  currentReport: null,
  generatedContent: null,
  isLoading: false,
  isGenerating: false,
  error: null,

  fetchReports: async (userId: number) => {
    set({ isLoading: true, error: null });
    try {
      const reports = await api.getReports(userId);
      set({ reports, isLoading: false });
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : '보고서 목록을 불러오는데 실패했습니다.';
      set({ error: message, isLoading: false });
    }
  },

  fetchReport: async (reportId: number) => {
    set({ isLoading: true, error: null });
    try {
      const report = await api.getReport(reportId);
      set({ currentReport: report, isLoading: false });
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : '보고서를 불러오는데 실패했습니다.';
      set({ error: message, isLoading: false });
    }
  },

  generateReport: async (params: GenerateReportParams) => {
    set({ isGenerating: true, error: null, generatedContent: null });
    try {
      const response = await api.generateReport(
        params.tasks,
        params.startDate,
        params.endDate,
        params.writer,
        params.email
      );

      // 모든 보고서를 하나의 문자열로 합침
      const combinedReport = response.reports
        .map((r) => `## Task ${r.task_id}\n\n${r.report}`)
        .join('\n\n---\n\n');

      set({
        generatedContent: combinedReport || '생성된 보고서가 없습니다.',
        isGenerating: false,
      });
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : '보고서 생성에 실패했습니다.';
      set({ error: message, isGenerating: false });
      throw error;
    }
  },

  setCurrentReport: (report: Report | null) => {
    set({ currentReport: report });
  },

  clearGeneratedContent: () => {
    set({ generatedContent: null });
  },

  clearError: () => {
    set({ error: null });
  },
}));
