import React, { useEffect, useState, useCallback } from 'react';
import './App.css';
import { Report, ReportFormData } from './types';
import Header from './components/Header';
import ReportForm from './components/ReportForm';
import ReportTable from './components/ReportTable';
import AuthModal from './components/AuthModal';

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
    }, []);

    const fetchWithAuth = useCallback(async (url: string, options: RequestInit = {}) => {
        const headers = new Headers(options.headers || {});
        headers.set('Content-Type', 'application/json');

        if (authToken) {
            headers.set('Authorization', `Bearer ${authToken}`);
        }

        const finalOptions: RequestInit = {
            ...options,
            headers: headers
        };

        const response = await fetch(url, finalOptions);

        if (response.status === 401) {
            handleLogout();
            throw new Error('Сессия истекла или недействительна. Пожалуйста, войдите снова.');
        }

        return response;
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
                        throw new Error(errorData.error || `Ошибка проверки токена: ${response.status} ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    setCurrentUser(data.user);
                    setIsAuthenticated(true);
                })
                .catch((err) => {
                    handleLogout();
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
                 if (response.status === 422) {
                    throw new Error(errorData.error || `Необрабатываемая сущность (422) при запросе отчетов.`);
                }
                throw new Error(errorData.error || `Ошибка сети при загрузке отчетов: ${response.statusText}`);
            }
            const data = await response.json();
            const validReports = (Array.isArray(data) ? data : []).map((report: any) => ({
                ...report,
                status: ['processing', 'completed', 'failed'].includes(report.status)
                    ? report.status
                    : 'processing',
                createdAt: report.createdAt || new Date().toISOString()
            }));
            setReports(validReports);
            setError(null);
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Не удалось загрузить отчеты';
            if (!message.includes('Сессия истекла')) {
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
        if (!isAuthenticated) {
            setError("Необходимо войти для создания отчета.");
            return;
        }
        setError(null);
        setIsLoading(true);
        try {
            const response = await fetchWithAuth('/api/generate-report', {
                method: 'POST',
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `Ошибка сервера при создании отчета: ${response.statusText}`);
            }

            const newReportData = await response.json();

            setReports(prevReports => [
                {
                    id: newReportData.id || `temp-${Date.now()}`,
                    githubUrl: newReportData.githubUrl || formData.githubUrl,
                    email: newReportData.email || formData.email,
                    dateRange: newReportData.dateRange || `${formData.startDate} - ${formData.endDate}`,
                    status: newReportData.status || 'processing',
                    createdAt: newReportData.createdAt || new Date().toISOString()
                },
                ...prevReports
            ]);

            setTimeout(fetchReports, 3000);

        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Не удалось создать отчет';
             if (!errorMessage.includes('Сессия истекла')) {
                 setError(errorMessage);
             }
        } finally {
            setIsLoading(false);
        }
    };

    const handleRegister = async (formData: Record<string, string>) => {
        setError(null);
        try {
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
            alert(data.message || 'Регистрация успешна! Теперь вы можете войти.');
            setIsLoginOpen(true);
        } catch (err) {
            throw err;
        }
    };

    const handleLogin = async (formData: Record<string, string>) => {
        setError(null);
        try {
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
        } catch (err) {
            throw err;
        }
    };

    if (authLoading) {
        return <div style={{ textAlign: 'center', margin: '4rem 0', fontSize: '1.2em' }}>Проверка авторизации...</div>;
    }

    return (
        <div className="container">
            <Header
                isAuthenticated={isAuthenticated}
                user={currentUser}
                onLoginClick={() => setIsLoginOpen(true)}
                onRegisterClick={() => setIsRegisterOpen(true)}
                onLogoutClick={handleLogout}
            />

            {error && !isLoginOpen && !isRegisterOpen && (
                <div style={{ color: 'red', background: '#ffebee', border: '1px solid red', borderRadius: '8px', padding: '1rem', textAlign: 'center', margin: '1rem 0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                   <span>Ошибка: {error}</span>
                    <button onClick={() => setError(null)} style={{ marginLeft: '10px', background: 'none', border: 'none', color: 'red', cursor: 'pointer', fontSize: '1.2em', padding: '0 5px' }}>✖</button>
                </div>
            )}

            {!isAuthenticated ? (
                <div className="card" style={{ textAlign: 'center', marginTop: '2rem' }}>
                    <h2>Добро пожаловать!</h2>
                    <p>Войдите или зарегистрируйтесь, чтобы начать генерировать отчеты по репозиториям GitHub.</p>
                </div>
            ) : (
                <>
                    <ReportForm onSubmit={handleGenerateReport} />
                    {isLoading && !reports.length ? (
                        <div style={{ textAlign: 'center', margin: '2rem 0' }}>Загрузка отчетов...</div>
                    ) : (
                        <ReportTable reports={reports} isLoading={isLoading} />
                    )}
                </>
            )}

            <AuthModal
                isOpen={isRegisterOpen}
                onClose={() => { setIsRegisterOpen(false); setError(null); }}
                onSubmit={handleRegister}
                title="Регистрация"
                submitButtonText="Зарегистрироваться"
            />

            <AuthModal
                isOpen={isLoginOpen}
                onClose={() => { setIsLoginOpen(false); setError(null); }}
                onSubmit={handleLogin}
                title="Вход"
                submitButtonText="Войти"
            />
        </div>
    );
};

export default App;