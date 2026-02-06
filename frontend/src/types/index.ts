// User types
export interface User {
  id: number;
  name: string;
  email: string;
  employee_number?: string;
  department?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  user_id: number;
  name: string;
  email: string;
}

// Task types
export interface Task {
  task_id: number;
  content: string;
  timestamp: string;
  sender: string;
  receiver: string;
  platform?: string;
  metadata?: Record<string, unknown>;
}

export interface TimelineResponse {
  tasks: Task[];
  total: number;
}

// Report types
export interface Report {
  id: number;
  user_id: number;
  title: string;
  content: string;
  start_date: string;
  end_date: string;
  created_at: string;
  status?: 'draft' | 'generated' | 'approved';
}

export interface GenerateReportRequest {
  user_id: number;
  start_date: string;
  end_date: string;
}

export interface GenerateReportResponse {
  report_id: number;
  title: string;
  content: string;
}

// Calendar types
export interface CalendarEvent {
  id: string;
  title: string;
  date: Date;
  type: 'task' | 'report' | 'meeting';
  color?: string;
}

export interface DateRange {
  start: Date;
  end: Date;
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}

export interface ApiError {
  status: number;
  message: string;
  details?: Record<string, unknown>;
}

// Table types
export interface Column<T> {
  key: keyof T | string;
  header: string;
  width?: string;
  render?: (value: T) => React.ReactNode;
}

export interface PaginationState {
  page: number;
  pageSize: number;
  total: number;
}

// Filter types
export interface TaskFilter {
  platform?: string;
  startDate?: string;
  endDate?: string;
  search?: string;
}
