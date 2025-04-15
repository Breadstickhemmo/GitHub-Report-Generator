import React from 'react';

interface User {
  id: number;
  username: string;
  email: string;
}

interface HeaderProps {
  isAuthenticated: boolean;
  user: User | null;
  onLoginClick: () => void;
  onRegisterClick: () => void;
  onLogoutClick: () => void;
}

const Header: React.FC<HeaderProps> = ({
  isAuthenticated,
  user,
  onLoginClick,
  onRegisterClick,
  onLogoutClick
}) => {
  return (
    <header className="header">
      <div className="header-content">
        <h1>GitHub Report Generator</h1>
        <p>Анализ качества кода репозиториев за выбранный период</p>
      </div>
      <div className="auth-buttons">
        {isAuthenticated ? (
          <>
            <span style={{ marginRight: '15px', color: '#333' }}>
                Привет, {user?.username || 'Пользователь'}!
            </span>
            <button
              className="secondary-btn"
              onClick={onLogoutClick}
            >
              Выход
            </button>
          </>
        ) : (
          <>
            <button
              className="secondary-btn"
              onClick={onLoginClick}
            >
              Вход
            </button>
            <button
              className="primary-btn"
              onClick={onRegisterClick}
            >
              Регистрация
            </button>
          </>
        )}
      </div>
    </header>
  );
};

export default Header;