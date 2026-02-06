import axios, { AxiosError, AxiosInstance } from 'axios';
import {
  LoginRequest,
  LoginResponse,
  Task,
  Report,
  GenerateReportRequest,
  GenerateReportResponse,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth APIs
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    // 백엔드는 JSON body를 기대함
    const response = await this.client.post<{
      success: boolean;
      user: { id: number; name: string; email: string };
    }>('/login', {
      email: credentials.email,
      password: credentials.password,
    });

    // 백엔드 응답 형식을 프론트엔드 형식으로 변환
    return {
      user_id: response.data.user.id,
      name: response.data.user.name,
      email: response.data.user.email,
    };
  }

  // User Timeline APIs
  async getUserTimeline(
    email: string,
    startDate: string,
    endDate: string
  ): Promise<Task[]> {
    // 백엔드 응답 타입 정의
    interface BackendActivity {
      source: string;
      timestamp: string;
      content: string;
      metadata: {
        sender: string;
        receiver: string;
        task_id: number;
        id: number;
      };
    }

    interface BackendTimelineResponse {
      user_id: string;
      start_date: string;
      end_date: string;
      activities: BackendActivity[];
      summary: Record<string, number>;
    }

    const response = await this.client.get<BackendTimelineResponse>(
      `/api/user-timeline/${encodeURIComponent(email)}`,
      {
        params: {
          start_date: startDate,
          end_date: endDate,
        },
      }
    );

    // 백엔드 응답을 프론트엔드 Task 형식으로 변환
    return response.data.activities.map((activity) => ({
      task_id: activity.metadata.id,
      content: activity.content,
      timestamp: activity.timestamp,
      sender: activity.metadata.sender,
      receiver: activity.metadata.receiver || '-',
      platform: activity.source,
      metadata: activity.metadata,
    }));
  }

  // Report APIs
  async generateReport(
    tasks: Task[],
    startDate: string,
    endDate: string,
    writer: string,
    email: string
  ): Promise<{ reports: Array<{ task_id: number; report: string }> }> {
    // tasks에서 platform별 ID 추출
    const platformIds: Record<string, number[]> = {
      slack: [],
      notion: [],
      onedrive: [],
      outlook: [],
    };

    tasks.forEach((task) => {
      const platform = task.platform?.toLowerCase();
      if (platform && platformIds[platform] && task.task_id) {
        platformIds[platform].push(task.task_id);
      }
    });

    const response = await this.client.post<{
      platform_ids: Record<string, number[]>;
      range: { start: string; end: string };
      reports: Array<{ task_id: number; report: string }>;
    }>('/reports/weekly', {
      platform_ids: platformIds,
      start: startDate,
      end: endDate,
      writer: writer,
      email: email,
    });

    return response.data;
  }

  async getReports(userId: number): Promise<Report[]> {
    const response = await this.client.get<Report[]>(`/user/${userId}/reports`);
    return response.data;
  }

  async getReport(reportId: number): Promise<Report> {
    const response = await this.client.get<Report>(`/report/${reportId}`);
    return response.data;
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    const response = await this.client.get<{ status: string }>('/health');
    return response.data;
  }
}

export const api = new ApiService();
export default api;
