import React, { useEffect, useState, useCallback } from 'react';
import './App.css';
import { Report, ReportFormData } from './types';
import Header from './components/Header';
import ReportForm from './components/ReportForm';
import ReportTable from './components/ReportTable';
import AuthModal from './components/AuthModal';

const App = () => {
  const [reports, setReports] = useState<Report[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [isLoginOpen, setIsLoginOpen] = useState(false);

  const fetchReports = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/reports');
      if (!response.ok) {
        throw new Error(`Ошибка сети: ${response.statusText}`);
      }
      const data = await response.json();
      const validReports = (Array.isArray(data) ? data : []).map((report: any) => ({
        ...report,
        status: ['processing', 'completed'].includes(report.status)
          ? report.status
          : 'processing'
      }));
      setReports(validReports);
    } catch (err) {
      console.error("Ошибка при загрузке отчетов:", err);
      setError(err instanceof Error ? err.message : 'Не удалось загрузить отчеты');
      setReports([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchReports();
    const intervalId = setInterval(fetchReports, 30000);
    return () => clearInterval(intervalId);
  }, [fetchReports]);

  const handleGenerateReport = async (formData: ReportFormData) => {
    setError(null);
    try {
      const response = await fetch('/api/generate-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
         const errorData = await response.json();
         throw new Error(errorData.error || `Ошибка сервера: ${response.statusText}`);
      }

      const newReportData = await response.json();

      setReports(prevReports => [
         {
           id: newReportData.reportId,
           githubUrl: formData.githubUrl,
           email: formData.email,
           dateRange: `${formData.startDate} - ${formData.endDate}`,
           status: 'processing',
           createdAt: new Date().toISOString()
         },
         ...prevReports
       ]);

      await fetchReports();

    } catch (err) {
      console.error("Ошибка при создании отчета:", err);
      setError(err instanceof Error ? err.message : 'Не удалось создать отчет');
       alert(`Ошибка при создании отчета: ${err instanceof Error ? err.message : 'Неизвестная ошибка'}`);
    }
  };

  const handleRegister = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Implement registration logic
    console.log('Регистрация...');
    setIsRegisterOpen(false);
  };

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Implement login logic
    console.log('Вход...');
    setIsLoginOpen(false);
  };

  return (
    <div className="container">
      <Header
        onLoginClick={() => setIsLoginOpen(true)}
        onRegisterClick={() => setIsRegisterOpen(true)}
      />

      {error && <div style={{ color: 'red', textAlign: 'center', margin: '1rem 0' }}>Ошибка: {error}</div>}

      <ReportForm onSubmit={handleGenerateReport} />

      {isLoading
        ? <div style={{ textAlign: 'center', margin: '2rem 0' }}>Загрузка отчетов...</div>
        : <ReportTable reports={reports} />
      }

      <AuthModal
        isOpen={isRegisterOpen}
        onClose={() => setIsRegisterOpen(false)}
        onSubmit={handleRegister}
        title="Регистрация"
        submitButtonText="Зарегистрироваться"
      >
        <div className="form-group">
          <label>Email</label>
          <input type="email" required />
        </div>
        <div className="form-group">
          <label>Имя пользователя</label>
          <input type="text" required />
        </div>
        <div className="form-group">
          <label>Пароль</label>
          <input type="password" required />
        </div>
        <div className="form-group">
          <label>Подтвердите пароль</label>
          <input type="password" required />
        </div>
      </AuthModal>

      <AuthModal
        isOpen={isLoginOpen}
        onClose={() => setIsLoginOpen(false)}
        onSubmit={handleLogin}
        title="Вход"
        submitButtonText="Войти"
      >
        <div className="form-group">
          <label>Email</label>
          <input type="email" required />
        </div>
        <div className="form-group">
          <label>Пароль</label>
          <input type="password" required />
        </div>
      </AuthModal>
    </div>
  );
};

export default App;