import React from 'react';
import { Report } from '../types'; 

interface ReportTableProps {
  reports: Report[];
  isLoading?: boolean;
}

const ReportTable: React.FC<ReportTableProps> = ({ reports, isLoading }) => {
  const handleDownload = (reportId: string) => {
    alert(`Загрузка отчета ${reportId} (еще не реализовано)`);
  };

  const getStatusText = (status: Report['status']) => {
      switch(status) {
          case 'processing': return 'В обработке...';
          case 'completed': return 'Завершен';
          case 'failed': return 'Ошибка';
          default: return 'Неизвестно';
      }
  };

  const getStatusStyle = (status: Report['status']) => {
      switch(status) {
          case 'processing': return { color: '#ffa000' };
          case 'completed': return { color: 'green' };
          case 'failed': return { color: 'red' };
          default: return {};
      }
  };


  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
         <h2>История запросов</h2>
         {isLoading && <span style={{ fontSize: '0.9em', color: '#777' }}>Обновление...</span>}
      </div>
      <table className="reports-table">
        <thead>
          <tr>
            <th>GitHub</th>
            <th>Email (автор коммитов)</th>
            <th>Статус</th>
            <th>Дата создания</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          {reports.length === 0 && !isLoading && (
            <tr>
              <td colSpan={5} style={{ textAlign: 'center' }}>Нет данных для отображения</td>
            </tr>
          )}
           {reports.length === 0 && isLoading && (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center' }}>Загрузка...</td>
              </tr>
           )}
          {reports.map(report => (
            <tr key={report.id}>
              <td>
                 <a href={report.githubUrl} target="_blank" rel="noopener noreferrer">{report.githubUrl.replace('https://github.com/', '')}</a>
              </td>
              <td>{report.email}</td>
              <td style={getStatusStyle(report.status)}>
                 {getStatusText(report.status)}
              </td>
              <td>
                {report.createdAt
                  ? new Date(report.createdAt).toLocaleString()
                  : "-"}
              </td>
              <td>
                <button
                  className="secondary-btn"
                  disabled={report.status !== 'completed'}
                  onClick={() => handleDownload(report.id)}
                  title={report.status !== 'completed' ? 'Отчет еще не готов' : 'Скачать отчет'}
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