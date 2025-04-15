export interface Report {
    id: string;
    githubUrl: string;
    email: string;
    dateRange: string;
    status: 'processing' | 'completed' | 'failed';
    createdAt: string;
  }

  export interface ReportFormData {
    githubUrl: string;
    email: string; // GitHub email
    startDate: string;
    endDate: string;
  }