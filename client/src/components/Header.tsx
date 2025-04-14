import React from 'react';

interface HeaderProps {
  onLoginClick: () => void;
  onRegisterClick: () => void;
}

const Header: React.FC<HeaderProps> = ({ onLoginClick, onRegisterClick }) => {
  return (
    <header className="header">
      <div className="header-content">
        <h1>GitHub Report Generator</h1>
        <p>Анализ качества кода репозиториев за выбранный период</p>
      </div>
      <div className="auth-buttons">
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
      </div>
    </header>
  );
};

export default Header;