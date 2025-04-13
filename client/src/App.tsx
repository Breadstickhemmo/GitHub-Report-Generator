import React, { useState, useEffect } from 'react';
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

  return (
    <div className="container">
      <header className="header">
        <h1>GitHub Report Generator</h1>
        <p>Анализ качества кода репозиториев за выбранный период</p>
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
            <label>Email для отправки</label>
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
    </div>
  );
};

export default App;