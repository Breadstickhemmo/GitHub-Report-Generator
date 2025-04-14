export interface Report {
    id: string;
    githubUrl: string;
    email: string;
    dateRange: string;
    status: 'processing' | 'completed';
    createdAt: string;
  }
  
  export interface ReportFormData {
    githubUrl: string;
    email: string;
    startDate: string;
    endDate: string;
  }