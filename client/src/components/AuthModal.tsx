import React, { useEffect } from 'react';
import { useForm, SubmitHandler, FieldErrors } from 'react-hook-form';
import { toast } from 'react-toastify';

type LoginFormInputs = {
  email: string;
  password: string;
};

type RegisterFormInputs = {
  email: string;
  username: string;
  password: string;
  confirm_password: string;
};

type AuthFormData = LoginFormInputs & Partial<RegisterFormInputs>;

type RegisterFieldErrors = FieldErrors<RegisterFormInputs>;

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (formData: AuthFormData) => Promise<void>;
  title: string;
  submitButtonText: string;
}

const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  title,
  submitButtonText,
}) => {
  const isRegister = title === 'Регистрация';

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
    watch,
  } = useForm<AuthFormData>({
    defaultValues: {
        email: "",
        password: "",
        username: "",
        confirm_password: ""
    }
  });

  const passwordValue = watch('password');

  useEffect(() => {
    if (isOpen) {
      reset({
        email: "",
        password: "",
        username: "",
        confirm_password: ""
      });
    }
  }, [isOpen, title, reset]);


  const handleFormSubmit: SubmitHandler<AuthFormData> = async (data) => {
    try {
       const cleanData = {...data};
       if (!isRegister) {
           delete cleanData.username;
           delete cleanData.confirm_password;
       }
       await onSubmit(cleanData);
    } catch (err) {
        toast.error(err instanceof Error ? err.message : 'Произошла неизвестная ошибка');
    }
  };

  const registerErrors = errors as RegisterFieldErrors;

  if (!isOpen) {
    return null;
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button
            onClick={onClose}
            style={{ position: 'absolute', top: '10px', right: '10px', background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer', lineHeight: '1', padding: '0' }}
            disabled={isSubmitting}
            aria-label="Закрыть"
        >
            ×
        </button>
        <h2>{title}</h2>
        <form onSubmit={handleSubmit(handleFormSubmit)} className="form" noValidate>

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
                type="email"
                id="email"
                className={errors.email ? 'input-error' : ''}
                {...register("email", {
                    required: "Email обязателен",
                    pattern: { value: /^\S+@\S+$/i, message: "Неверный формат email" }
                })}
                disabled={isSubmitting}
                autoComplete="email"
            />
             {errors.email && <span className="error-message">{errors.email.message}</span>}
          </div>

          {isRegister && (
            <div className="form-group">
              <label htmlFor="username">Имя пользователя</label>
              <input
                type="text"
                id="username"
                className={registerErrors.username ? 'input-error' : ''}
                {...register("username", { required: isRegister ? "Имя пользователя обязательно" : false })}
                disabled={isSubmitting}
                autoComplete="username"
              />
              {registerErrors.username && <span className="error-message">{registerErrors.username.message}</span>}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="password">Пароль</label>
            <input
                type="password"
                id="password"
                className={errors.password ? 'input-error' : ''}
                {...register("password", { required: "Пароль обязателен" })}
                disabled={isSubmitting}
                autoComplete={isRegister ? "new-password" : "current-password"}
            />
            {errors.password && <span className="error-message">{errors.password.message}</span>}
          </div>

          {isRegister && (
            <div className="form-group">
              <label htmlFor="confirm_password">Подтвердите пароль</label>
              <input
                type="password"
                id="confirm_password"
                className={registerErrors.confirm_password ? 'input-error' : ''}
                {...register("confirm_password", {
                    required: isRegister ? "Подтверждение пароля обязательно" : false,
                    validate: value => isRegister ? (value === passwordValue || "Пароли не совпадают") : true
                })}
                disabled={isSubmitting}
                autoComplete="new-password"
               />
               {registerErrors.confirm_password && <span className="error-message">{registerErrors.confirm_password.message}</span>}
            </div>
          )}

          <button type="submit" className="primary-btn" disabled={isSubmitting} style={{marginTop: '1rem'}}>
            {isSubmitting ? 'Обработка...' : submitButtonText}
          </button>
        </form>
      </div>
    </div>
  );
};

export default AuthModal;