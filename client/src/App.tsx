import React, { useEffect, useState } from 'react';
import './App.css';

interface Report {
  id: string;
  githubUrl: string;
  email: string;
  dateRange: string;
  status: 'processing' | 'completed';
  createdAt: string;
}

const App = () => {
  const [githubUrl, setGithubUrl] = useState('');
  const [email, setEmail] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [reports, setReports] = useState<Report[]>([]);

  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [isLoginOpen, setIsLoginOpen] = useState(false);

  useEffect(() => {
    fetch('/api/reports')
      .then(res => res.json())
      .then(data => {
        const validReports = data.map((report: any) => ({
          ...report,
          status: ['processing', 'completed'].includes(report.status)
            ? report.status
            : 'processing'
        }));
        setReports(validReports);
      });
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const newReport: Report = {
      id: Date.now().toString(),
      githubUrl,
      email,
      dateRange: `${startDate} - ${endDate}`,
      status: 'processing',
      createdAt: ""
    };

    try {
      await fetch('/api/generate-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ githubUrl, email, startDate, endDate })
      });
      
      setReports([newReport, ...reports]);
      setGithubUrl('');
      setEmail('');
      setStartDate('');
      setEndDate('');
    } catch (error) {
      alert('Ошибка при создании отчета');
    }
  };

  const handleRegister = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Регистрация');
    setIsRegisterOpen(false);
  };

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Вход');
    setIsLoginOpen(false);
  };

  return (
    <div className="container">
      <header className="header">
        <div className="header-content">
          <h1>GitHub Report Generator</h1>
          <p>Анализ качества кода репозиториев за выбранный период</p>
        </div>
        <div className="auth-buttons">
          <button 
            className="secondary-btn" 
            onClick={() => setIsLoginOpen(true)}
          >
            Вход
          </button>
          <button 
            className="primary-btn" 
            onClick={() => setIsRegisterOpen(true)}
          >
            Регистрация
          </button>
        </div>
      </header>

      <div className="card">
        <form onSubmit={handleSubmit} className="form">
          <div className="form-group">
            <label>GitHub репозиторий</label>
            <input
              type="url"
              placeholder="https://github.com/..."
              value={githubUrl}
              onChange={(e) => setGithubUrl(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label>Email пользователя GitHub</label>
            <input
              type="email"
              placeholder="example@domain.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="date-group">
            <div className="date-field">
              <label>Дата начала</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                required
              />
            </div>
            <div className="date-field">
              <label>Дата окончания</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                required
              />
            </div>
          </div>

          <button type="submit" className="primary-btn">
            Сформировать отчет
          </button>
        </form>
      </div>

      <div className="card">
        <h2>История запросов</h2>
        <table className="reports-table">
          <thead>
            <tr>
              <th>GitHub</th>
              <th>Email</th>
              <th>Статус</th>
              <th>Дата создания</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            {reports.map(report => (
              <tr key={report.id}>
                <td>{report.githubUrl}</td>
                <td>{report.email}</td>
                <td>
                  {report.status === 'processing' 
                    ? 'В обработке...' 
                    : 'Завершен'}
                </td>
                <td>
                  {report.createdAt 
                    ? new Date(report.createdAt).toLocaleDateString()
                    : "-"}
                </td>
                <td>
                  <button 
                    className="secondary-btn"
                    disabled={report.status !== 'completed'}
                  >
                    Скачать
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Модальное окно регистрации */}
      {isRegisterOpen && (
        <div className="modal-overlay" onClick={() => setIsRegisterOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Регистрация</h2>
            <form onSubmit={handleRegister} className="form">
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
              <button type="submit" className="primary-btn">
                Зарегистрироваться
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Модальное окно входа */}
      {isLoginOpen && (
        <div className="modal-overlay" onClick={() => setIsLoginOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Вход</h2>
            <form onSubmit={handleLogin} className="form">
              <div className="form-group">
                <label>Email</label>
                <input type="email" required />
              </div>
              <div className="form-group">
                <label>Пароль</label>
                <input type="password" required />
              </div>
              <button type="submit" className="primary-btn">
                Войти
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;