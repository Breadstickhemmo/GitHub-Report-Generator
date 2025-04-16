import React from 'react';
import { useForm, SubmitHandler } from 'react-hook-form';
import { ReportFormData } from '../types';
import { toast } from 'react-toastify';

interface ReportFormProps {
  onSubmit: (formData: ReportFormData) => Promise<void>;
}

const ReportForm: React.FC<ReportFormProps> = ({ onSubmit }) => {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
    watch
  } = useForm<ReportFormData>({
    defaultValues: {
        githubUrl: "",
        email: "",
        startDate: "",
        endDate: ""
    }
  });

  const startDateValue = watch("startDate");

  const handleFormSubmit: SubmitHandler<ReportFormData> = async (data) => {
    try {
      await onSubmit(data);
      reset();
    } catch (error) {
      console.error("Error during form submission:", error);
      toast.error("Не удалось отправить форму. Попробуйте снова.");
    }
  };

  return (
    <div className="card">
      <form onSubmit={handleSubmit(handleFormSubmit)} className="form" noValidate>
        <div className="form-group">
          <label htmlFor="githubUrl">GitHub репозиторий</label>
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
          {errors.githubUrl && <span className="error-message">{errors.githubUrl.message}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="email">Email пользователя GitHub</label>
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
                    return new Date(value) >= new Date(startDateValue) || "Дата окончания не может быть раньше даты начала";
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