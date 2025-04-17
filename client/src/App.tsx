// src/App.tsx
import React, { useEffect, useState, useCallback } from 'react';
import './App.css';
import 'react-toastify/dist/ReactToastify.css';
import { Report, ReportFormData } from './types';
import Header from './components/Header';
import ReportForm from './components/ReportForm';
import ReportTable from './components/ReportTable';
import AuthModal from './components/AuthModal';
import { ToastContainer, toast } from 'react-toastify';
import { fetchWithAuth as fetchWithAuthHelper } from './utils/fetchWithAuth';

interface User {
    id: number;
    username: string;
    email: string;
}

const App = () => {
    const [reports, setReports] = useState<Report[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
    const [authToken, setAuthToken] = useState<string | null>(null);
    const [currentUser, setCurrentUser] = useState<User | null>(null);
    const [authLoading, setAuthLoading] = useState<boolean>(true);
    const [isRegisterOpen, setIsRegisterOpen] = useState(false);
    const [isLoginOpen, setIsLoginOpen] = useState(false);

    const handleLogout = useCallback(() => {
        localStorage.removeItem('authToken');
        setAuthToken(null);
        setCurrentUser(null);
        setIsAuthenticated(false);
        setReports([]);
        setError(null);
        toast.info("Вы вышли из системы.");
    }, []);

    const fetchWithAuth = useCallback(async (url: string, options: RequestInit = {}) => {
        try {
            return await fetchWithAuthHelper(url, options, handleLogout);
        } catch (error) {
            if (error instanceof Error && error.message.includes('401')) {
                 // Toast might be handled within fetchWithAuthHelper or here if needed
            } else if (error instanceof Error) {
                 toast.error(`Сетевая ошибка: ${error.message}`);
            } else {
                 toast.error("Неизвестная сетевая ошибка.");
            }
            throw error;
        }
    }, [authToken, handleLogout]);


    useEffect(() => {
        const tokenFromStorage = localStorage.getItem('authToken');
        if (tokenFromStorage) {
            setAuthToken(tokenFromStorage);
        } else {
            setAuthLoading(false);
        }
    }, []);

    useEffect(() => {
        if (authToken) {
            setAuthLoading(true);
            fetchWithAuth('/api/me')
                .then(async response => {
                    if (!response.ok) {
                        const errorData = await response.json().catch(() => ({}));
                        if (response.status !== 401) {
                            throw new Error(errorData.error || `Ошибка проверки токена: ${response.status} ${response.statusText}`);
                        }
                        return null;
                    }
                    return response.json();
                })
                .then(data => {
                    if (data) {
                        setCurrentUser(data.user);
                        setIsAuthenticated(true);
                    }
                })
                .catch((err) => {
                     if (!(err instanceof Error && err.message.includes('401'))) {
                        console.error("Error fetching /api/me, logging out:", err);
                     }
                })
                .finally(() => {
                    setAuthLoading(false);
                });
        } else {
             setAuthLoading(false);
        }
    }, [authToken, fetchWithAuth, handleLogout]);


    const fetchReports = useCallback(async () => {
        if (!isAuthenticated || !authToken) {
            return;
        };

        setIsLoading(true);
        try {
            const response = await fetchWithAuth('/api/reports');
            if (!response.ok) {
                 const errorData = await response.json().catch(() => ({}));
                 throw new Error(errorData.error || `Ошибка сети при загрузке отчетов: ${response.statusText}`);
            }
            const data: Report[] = await response.json();

            const validReports = Array.isArray(data) ? data.map(report => ({
                ...report,
                status: ['processing', 'completed', 'failed'].includes(report.status) ? report.status : 'processing',
                createdAt: report.createdAt || new Date().toISOString(),
                llm_status: report.llm_status || 'pending',
                hasPdf: report.hasPdf || false
            })) : [];

            setReports(validReports);
            setError(null);
        } catch (err) {
             if (!(err instanceof Error && err.message.includes('401'))) {
                const message = err instanceof Error ? err.message : 'Не удалось загрузить отчеты';
                setError(message);
             }
        } finally {
            setIsLoading(false);
        }
    }, [isAuthenticated, authToken, fetchWithAuth]);


    useEffect(() => {
        let intervalId: NodeJS.Timeout | null = null;
        if (isAuthenticated && authToken) {
            fetchReports();
            intervalId = setInterval(fetchReports, 30000);
        } else {
             setReports([]);
        }

        return () => {
            if (intervalId) {
                clearInterval(intervalId);
            }
        };
    }, [isAuthenticated, authToken, fetchReports]);


    const handleGenerateReport = async (formData: ReportFormData) => {
        setError(null);
        try {
            const response = await fetchWithAuth('/api/generate-report', {
                method: 'POST',
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `Ошибка сервера при создании отчета: ${response.statusText}`);
            }

            const newReportData: Report = await response.json();

            toast.success("Запрос на создание отчета отправлен!");

            setReports(prevReports => [
                {
                    id: newReportData.id || `temp-${Date.now()}`,
                    githubUrl: newReportData.githubUrl || formData.githubUrl,
                    email: newReportData.email || formData.email,
                    dateRange: newReportData.dateRange || `${formData.startDate} - ${formData.endDate}`,
                    status: newReportData.status || 'processing',
                    createdAt: newReportData.createdAt || new Date().toISOString(),
                    llm_status: newReportData.llm_status || 'pending',
                    hasPdf: newReportData.hasPdf || false
                },
                ...prevReports
            ]);

            setTimeout(fetchReports, 5000);

        } catch (err) {
              const errorMessage = err instanceof Error ? err.message : 'Не удалось создать отчет';
              if (!(err instanceof Error && err.message.includes('401'))) {
                   setError(errorMessage);
                   toast.error(errorMessage);
              }
        } finally {
        }
    };


    const handleRegister = async (formData: Record<string, string>) => {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Ошибка регистрации');
        }
        setIsRegisterOpen(false);
        toast.success(data.message || 'Регистрация успешна! Теперь вы можете войти.');
        setIsLoginOpen(true);
    };

    const handleLogin = async (formData: Record<string, string>) => {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Ошибка входа');
        }
        if (!data.access_token || !data.user) {
             throw new Error('Сервер не вернул токен или данные пользователя');
        }
        localStorage.setItem('authToken', data.access_token);
        setAuthToken(data.access_token);
        setCurrentUser(data.user);
        setIsAuthenticated(true);
        setIsLoginOpen(false);
        toast.success(`Добро пожаловать, ${data.user.username}!`);
    };


    if (authLoading) {
        return <div style={{ textAlign: 'center', margin: '4rem 0', fontSize: '1.2em' }}>Проверка авторизации...</div>;
    }

    const closeLoginModal = () => {
        setIsLoginOpen(false);
        setError(null);
    };

    const closeRegisterModal = () => {
        setIsRegisterOpen(false);
        setError(null);
    };

    return (
      <div className="container">
          <Header
              isAuthenticated={isAuthenticated}
              user={currentUser}
              onLoginClick={() => setIsLoginOpen(true)}
              onRegisterClick={() => setIsRegisterOpen(true)}
              onLogoutClick={handleLogout}
          />

          {!isAuthenticated ? (
              <>
                  <div className="card" style={{ textAlign: 'center', marginTop: '2rem' }}>
                      <h2>Добро пожаловать!</h2>
                      <p>Войдите или зарегистрируйтесь, чтобы начать генерировать отчеты по репозиториям GitHub.</p>
                  </div>

                  <div className="welcome-info card">
                      <h3>Что это за приложение?</h3>
                      <p style={{ textAlign: 'center'}}>
                          Это сервис для автоматического анализа качества кода разработчиков
                          в GitHub-репозиториях. Приложение помогает оценить код, написанный
                          конкретным автором за выбранный период времени.
                      </p>
                      <h4>Как это работает:</h4>
                      <ul>
                          <li>
                              Вы указываете публичный репозиторий на GitHub, email автора коммитов
                              и временной интервал для анализа.
                          </li>
                          <li>
                              Сервис загружает соответствующие файлы с кодом из истории коммитов.
                          </li>
                          <li>
                              Собранные данные отправляются AI-модели (YandexGPT) для глубокого анализа
                              на предмет потенциальных ошибок, уязвимостей, соответствия кодстайлу
                              и архитектурных проблем.
                          </li>
                          <li>
                              На основе ответа AI формируется отчет, который вы можете скачать
                              для дальнейшего изучения и отслеживания динамики качества кода.
                          </li>
                      </ul>
                  </div>
              </>
          ) : (
              <>
                  <ReportForm onSubmit={handleGenerateReport} />
                  {isLoading && reports.length === 0 ? (
                      <div style={{ textAlign: 'center', margin: '2rem 0' }}>Загрузка истории отчетов...</div>
                  ) : (
                      <ReportTable
                          reports={reports}
                          isLoading={isLoading}
                          fetchWithAuth={fetchWithAuth}
                      />
                  )}
              </>
          )}

            <AuthModal
                isOpen={isRegisterOpen}
                onClose={closeRegisterModal}
                onSubmit={handleRegister}
                title="Регистрация"
                submitButtonText="Зарегистрироваться"
            />

            <AuthModal
                isOpen={isLoginOpen}
                onClose={closeLoginModal}
                onSubmit={handleLogin}
                title="Вход"
                submitButtonText="Войти"
            />

            <ToastContainer
                position="bottom-right"
                autoClose={5000}
                hideProgressBar={false}
                newestOnTop={false}
                closeOnClick
                rtl={false}
                pauseOnFocusLoss
                draggable
                pauseOnHover
                theme="colored"
            />
        </div>
    );
};

export default App;