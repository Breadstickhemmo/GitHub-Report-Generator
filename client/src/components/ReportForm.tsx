import React, { useState } from 'react';
import { ReportFormData } from '../types';

interface ReportFormProps {
  onSubmit: (formData: ReportFormData) => Promise<void>;
}

const ReportForm: React.FC<ReportFormProps> = ({ onSubmit }) => {
  const [githubUrl, setGithubUrl] = useState('');
  const [email, setEmail] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit({ githubUrl, email, startDate, endDate });
    setGithubUrl('');
    setEmail('');
    setStartDate('');
    setEndDate('');
  };

  return (
    <div className="card">
      <form onSubmit={handleSubmit} className="form">
        <div className="form-group">
          <label>GitHub репозиторий</label>
          <input
            type="url"
            placeholder="https://github.com/owner/repo"
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
  );
};

export default ReportForm;