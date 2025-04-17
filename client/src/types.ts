export interface Report {
  id: string;
  githubUrl: string;
  email: string;
  dateRange: string;
  status: 'processing' | 'completed' | 'failed';
  createdAt: string;
  llm_status?: 'pending' | 'processing' | 'completed' | 'failed' | 'skipped';
  hasPdf?: boolean;
}

export interface ReportFormData {
  githubUrl: string;
  email: string;
  startDate: string;
  endDate: string;
}