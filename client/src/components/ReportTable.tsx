import React from 'react';
import { Report } from '../types';

interface ReportTableProps {
  reports: Report[];
}

const ReportTable: React.FC<ReportTableProps> = ({ reports }) => {
  const handleDownload = (reportId: string) => {
    alert(`Загрузка отчета ${reportId} (еще не реализовано)`);
  };

  return (
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
          {reports.length === 0 && (
            <tr>
              <td colSpan={5} style={{ textAlign: 'center' }}>Нет данных для отображения</td>
            </tr>
          )}
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
                  onClick={() => handleDownload(report.id)}
                >
                  Скачать
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ReportTable;