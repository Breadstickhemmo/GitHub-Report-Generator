import React from 'react';
import { useForm, SubmitHandler } from 'react-hook-form';
import { ReportFormData } from '../types';
import { toast } from 'react-toastify';

const ClearIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
    </svg>
);


interface ReportFormProps {
  onSubmit: (formData: ReportFormData) => Promise<void>;
}

const ReportForm: React.FC<ReportFormProps> = ({ onSubmit }) => {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
    watch,
    setValue,
  } = useForm<ReportFormData>({
    mode: 'onBlur',
    defaultValues: {
        githubUrl: "",
        email: "",
        startDate: "",
        endDate: ""
    }
  });

  const startDateValue = watch("startDate");
  const githubUrlValue = watch("githubUrl");
  const emailValue = watch("email");

  const handleFormSubmit: SubmitHandler<ReportFormData> = async (data) => {
    try {
      await onSubmit(data);
      reset();
    } catch (error) {
      toast.error("Не удалось отправить форму. Попробуйте снова.");
    }
  };

   const handleClearInput = (fieldName: keyof ReportFormData) => {
      setValue(fieldName, '', { shouldValidate: true, shouldDirty: true });
  };

  return (
    <div className="card">
      <form onSubmit={handleSubmit(handleFormSubmit)} className="form" noValidate>
        <div className="form-group">
          <label htmlFor="githubUrl">GitHub репозиторий</label>
          <div className="input-wrapper">
              <input
                type="url"
                id="githubUrl"
                placeholder="https://github.com/owner/repo"
                className={errors.githubUrl ? 'input-error' : ''}
                {...register("githubUrl", {
                  required: "URL репозитория обязателен",
                  pattern: {
                    value: /^https:\/\/github\.com\/[^/]+\/[^/]+(\/)?$/i,
                    message: "Неверный формат URL GitHub (https://github.com/owner/repo)"
                  }
                })}
                disabled={isSubmitting}
              />
               {githubUrlValue && !isSubmitting && (
                    <button
                      type="button"
                      className="clear-input-btn"
                      onClick={() => handleClearInput('githubUrl')}
                      aria-label="Очистить URL репозитория"
                      title="Очистить URL репозитория"
                    >
                      <ClearIcon />
                    </button>
                )}
          </div>
          {errors.githubUrl && <span className="error-message">{errors.githubUrl.message}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="email">Email пользователя GitHub</label>
           <div className="input-wrapper">
              <input
                type="email"
                id="email"
                placeholder="example@domain.com"
                className={errors.email ? 'input-error' : ''}
                {...register("email", {
                  required: "Email обязателен",
                  pattern: {
                    value: /^\S+@\S+$/i,
                    message: "Неверный формат email"
                  }
                })}
                disabled={isSubmitting}
              />
               {emailValue && !isSubmitting && (
                    <button
                      type="button"
                      className="clear-input-btn"
                      onClick={() => handleClearInput('email')}
                      aria-label="Очистить Email"
                      title="Очистить Email"
                    >
                      <ClearIcon />
                    </button>
                )}
           </div>
          {errors.email && <span className="error-message">{errors.email.message}</span>}
        </div>

        <div className="date-group">
          <div className="date-field">
            <label htmlFor="startDate">Дата начала</label>
            <input
              type="date"
              id="startDate"
              className={errors.startDate ? 'input-error' : ''}
              {...register("startDate", { required: "Дата начала обязательна" })}
              disabled={isSubmitting}
            />
             {errors.startDate && <span className="error-message">{errors.startDate.message}</span>}
          </div>
          <div className="date-field">
            <label htmlFor="endDate">Дата окончания</label>
            <input
              type="date"
              id="endDate"
              className={errors.endDate ? 'input-error' : ''}
              {...register("endDate", {
                required: "Дата окончания обязательна",
                validate: value => {
                    if (!startDateValue) return true;
                    const start = new Date(startDateValue);
                    const end = new Date(value);
                    if (isNaN(start.getTime()) || isNaN(end.getTime())) return true;

                    return end >= start || "Дата окончания не может быть раньше даты начала";
                }
              })}
              disabled={isSubmitting}
            />
            {errors.endDate && <span className="error-message">{errors.endDate.message}</span>}
          </div>
        </div>

        <button type="submit" className="primary-btn" disabled={isSubmitting} style={{marginTop: '1rem'}}>
          {isSubmitting ? 'Генерация...' : 'Сформировать отчет'}
        </button>
      </form>
    </div>
  );
};

export default ReportForm;