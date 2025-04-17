// src/components/ReportTable.tsx

import React from 'react';
import { Report } from '../types';
import { toast } from 'react-toastify';

interface ReportTableProps {
  reports: Report[];
  isLoading?: boolean;
  fetchWithAuth: (url: string, options?: RequestInit) => Promise<Response>;
}

const ReportTable: React.FC<ReportTableProps> = ({ reports, isLoading, fetchWithAuth }) => {

  const handleDownload = async (reportId: string, githubUrl: string) => {
    toast.info(`Запрос на скачивание отчета ${reportId}...`);
    try {
        const response = await fetchWithAuth(`/api/reports/${reportId}/download`);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.description || errorData.error || `Ошибка скачивания: ${response.statusText}`);
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        const repoName = githubUrl.split('/').pop() || 'repo';
        const shortId = reportId.substring(0, 8);
        a.download = `CodeAnalysis_${repoName}_${shortId}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
        toast.success(`Отчет ${reportId} успешно скачан.`);

    } catch (err) {
         const message = err instanceof Error ? err.message : 'Не удалось скачать отчет.';
         if (!(err instanceof Error && (err.message.includes('401') || err.message.startsWith('Сетевая ошибка:')))) {
            toast.error(message);
         }
         console.error("Download error:", err);
    }
  };

  const getStatusText = (status: Report['status'], llm_status: Report['llm_status']) => {
      switch(status) {
          case 'processing':
              if (llm_status === 'processing') return 'Анализ AI...';
              if (llm_status === 'pending') return 'Обработка GitHub...';
              return 'В обработке...';
          case 'completed': return 'Готов';
          case 'failed': return 'Ошибка';
          default: return 'Неизвестно';
      }
  };

  const getStatusStyle = (status: Report['status']) => {
      switch(status) {
          case 'processing': return { color: '#ffa000', fontWeight: '500' };
          case 'completed': return { color: 'green', fontWeight: '500' };
          case 'failed': return { color: 'red', fontWeight: '500' };
          default: return {};
      }
  };


  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
         <h2>История запросов</h2>
         {isLoading && <span style={{ fontSize: '0.9em', color: '#777' }}>Обновление...</span>}
      </div>
      <div style={{ overflowX: 'auto' }}>
          <table className="reports-table">
            <thead>
              <tr>
                <th>Репозиторий</th>
                <th>Автор</th>
                <th>Статус</th>
                <th>Запрошен</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              {reports.length === 0 && !isLoading && (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '20px' }}>Нет данных для отображения. Сформируйте свой первый отчет!</td>
                </tr>
              )}
              {reports.length === 0 && isLoading && (
                  <tr>
                    <td colSpan={5} style={{ textAlign: 'center', padding: '20px' }}>Загрузка истории...</td>
                  </tr>
              )}
              {reports.map(report => (
                <tr key={report.id}>
                  <td>
                     <a href={report.githubUrl} target="_blank" rel="noopener noreferrer" title={report.githubUrl}>
                        {report.githubUrl.replace('https://github.com/', '').split('/').slice(0, 2).join('/')}
                    </a>
                  </td>
                  <td title={report.email}>{report.email}</td>
                  <td style={getStatusStyle(report.status)}>
                     {getStatusText(report.status, report.llm_status)}
                  </td>
                  <td>
                    {report.createdAt
                      ? new Date(report.createdAt).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
                      : "-"}
                  </td>
                  <td>
                    <button
                      className="secondary-btn"
                      disabled={report.status !== 'completed' || !report.hasPdf}
                      onClick={() => handleDownload(report.id, report.githubUrl)}
                      title={report.status !== 'completed' ? 'Отчет еще не готов' : (!report.hasPdf ? 'Ошибка генерации PDF' : 'Скачать PDF отчет')}
                    >
                      Скачать PDF
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

export default ReportTable;