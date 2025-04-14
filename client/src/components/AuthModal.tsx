import React from 'react';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (e: React.FormEvent) => void;
  title: string;
  submitButtonText: string;
  children: React.ReactNode;
}

const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  title,
  submitButtonText,
  children
}) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h2>{title}</h2>
        <form onSubmit={onSubmit} className="form">
          {children} {/* Здесь будут поля email/password/username */}
          <button type="submit" className="primary-btn">
            {submitButtonText}
          </button>
        </form>
      </div>
    </div>
  );
};

export default AuthModal;