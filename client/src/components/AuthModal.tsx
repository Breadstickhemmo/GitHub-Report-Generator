// --- START OF FILE AuthModal.tsx ---

import React, { useState, useEffect } from 'react';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (formData: Record<string, string>) => Promise<void>;
  title: string;
  submitButtonText: string;
  children?: React.ReactNode;
}

const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  title,
  submitButtonText,
}) => {
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setFormData({});
      setError(null);
      setIsSubmitting(false);
    }
  }, [isOpen, title]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
       if (title === 'Регистрация' && formData.password !== formData.confirm_password) {
           throw new Error('Пароли не совпадают');
       }
       await onSubmit(formData);
    } catch (err) {
        setError(err instanceof Error ? err.message : 'Произошла ошибка');
    } finally {
        setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  const isRegister = title === 'Регистрация';

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button onClick={onClose} style={{ position: 'absolute', top: '10px', right: '10px', background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer' }}>×</button>
        <h2>{title}</h2>
        {error && <p style={{ color: 'red', textAlign: 'center', marginBottom: '1rem' }}>{error}</p>}
        <form onSubmit={handleSubmit} className="form">

          <div className="form-group">
            <label>Email</label>
            <input type="email" name="email" required onChange={handleChange} value={formData.email || ''} disabled={isSubmitting}/>
          </div>

          {isRegister && (
            <div className="form-group">
              <label>Имя пользователя</label>
              <input type="text" name="username" required onChange={handleChange} value={formData.username || ''} disabled={isSubmitting}/>
            </div>
          )}

          <div className="form-group">
            <label>Пароль</label>
            <input type="password" name="password" required onChange={handleChange} value={formData.password || ''} disabled={isSubmitting}/>
          </div>

          {isRegister && (
            <div className="form-group">
              <label>Подтвердите пароль</label>
              <input type="password" name="confirm_password" required onChange={handleChange} value={formData.confirm_password || ''} disabled={isSubmitting}/>
            </div>
          )}

          <button type="submit" className="primary-btn" disabled={isSubmitting}>
            {isSubmitting ? 'Обработка...' : submitButtonText}
          </button>
        </form>
      </div>
    </div>
  );
};

export default AuthModal;