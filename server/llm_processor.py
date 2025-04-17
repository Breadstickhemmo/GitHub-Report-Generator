from __future__ import annotations
from yandex_cloud_ml_sdk import YCloudML
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import requests
from io import BytesIO
from collections import defaultdict
import logging
import os

logger = logging.getLogger(__name__)


class PDFGenerator:
    @staticmethod
    def _download_font(font_url):
        try:
            response = requests.get(font_url, timeout=10)
            response.raise_for_status()
            return BytesIO(response.content)
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка загрузки шрифта {font_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка загрузки шрифта: {e}")
            return None

    @staticmethod
    def save_to_pdf(filename: str, title: str, content: str):
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        font_urls = {
            'Roboto': 'https://github.com/googlefonts/roboto/blob/main/src/hinted/Roboto-Regular.ttf?raw=true',
            'Roboto-Bold': 'https://github.com/googlefonts/roboto/blob/main/src/hinted/Roboto-Bold.ttf?raw=true'
        }

        registered_fonts = pdfmetrics.getRegisteredFontNames()
        fonts_to_register = {}

        for name, url in font_urls.items():
            if name not in registered_fonts:
                fonts_to_register[name] = url

        for name, url in fonts_to_register.items():
            try:
                font_data = PDFGenerator._download_font(url)
                if font_data:
                    pdfmetrics.registerFont(TTFont(name, font_data))
                    logger.info(f"Шрифт {name} успешно зарегистрирован.")
                else:
                    logger.warning(f"Не удалось загрузить данные для шрифта {name}.")
            except Exception as e:
                logger.error(f"Не удалось зарегистрировать шрифт {name}: {e}")

        if 'Roboto' in pdfmetrics.getRegisteredFontNames():
            font_name = 'Roboto'
            bold_font_name = 'Roboto-Bold'
        else:
            logger.warning("Шрифт Roboto недоступен. Используем стандартный шрифт (возможны проблемы с кириллицей).")
            font_name = 'Helvetica'
            bold_font_name = 'Helvetica-Bold'


        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontName=bold_font_name,
            fontSize=14,
            alignment=1,
            spaceAfter=20,
            textColor=colors.darkblue
        )

        text_style = ParagraphStyle(
            'Text',
            parent=styles['BodyText'],
            fontName=font_name,
            fontSize=10,
            leading=14,
            spaceAfter=12
        )

        story = []
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 12))

        def clean_text(text):
            if not isinstance(text, str):
                text = str(text)
            return text.replace('\x00', '').replace('\ufffd', '').replace('\r', '')

        for paragraph in content.split('\n\n'):
            safe_paragraph = clean_text(paragraph)
            if safe_paragraph.strip():
                try:
                    story.append(Paragraph(safe_paragraph, text_style))
                    story.append(Spacer(1, 8))
                except Exception as para_err:
                    logger.error(f"Ошибка добавления параграфа в PDF: {para_err}. Параграф: '{safe_paragraph[:100]}...'")
                    story.append(Paragraph(f"[Ошибка рендеринга параграфа: {para_err}]", text_style))
                    story.append(Spacer(1, 8))

        try:
            doc.build(story)
            logger.info(f"PDF успешно создан: {filename}")
        except Exception as build_err:
             logger.error(f"Ошибка сборки PDF документа {filename}: {build_err}", exc_info=True)
             raise


class CodeAnalyzer:
    def __init__(self, folder_id: str, auth_token: str):
        if not folder_id or not auth_token:
            raise ValueError("Yandex Folder ID and Auth Token are required.")
        try:
            self.sdk = YCloudML(
                folder_id=folder_id,
                auth=auth_token,
            )
            logger.info("YCloudML SDK инициализирован успешно.")
        except Exception as e:
             logger.error(f"Ошибка инициализации YCloudML SDK: {e}", exc_info=True)
             raise

        self.analysis_results = []
        self.summaries = []
        self.authors_stats = defaultdict(list)
        self.total_files = 0
        self.completed_files = 0
        self.partial_files = 0
        self.incomplete_files = 0

    def analyze_code(self, code, filename, author_email):
        MAX_CODE_LEN = 5500
        truncated_code = code[:MAX_CODE_LEN]
        if len(code) > MAX_CODE_LEN:
             logger.warning(f"Код файла {filename} обрезан до {MAX_CODE_LEN} символов для анализа.")

        messages = [
             {
                "role": "system",
                "text": "Ты - опытный разработчик (уровень Senior). Проанализируй код по критериям:\n"
                        "1. Качество кода (стиль, читаемость, соответствие PEP8/стандартам языка)\n"
                        "2. Потенциальные проблемы (баги, узкие места производительности, гонки данных, утечки ресурсов)\n"
                        "3. Уязвимости безопасности (SQL-инъекции, XSS, небезопасная обработка данных)\n"
                        "4. Архитектурные недочеты (нарушение SOLID, связанность, связность)\n"
                        "5. Возможности улучшения (рефакторинг, использование лучших практик, тесты)\n\n"
                        "Определи статус файла по следующим правилам:\n"
                        "- [STATUS: COMPLETED] - если код полностью готов и соответствует стандартам:\n"
                        "  * Реализует всю заявленную функциональность\n"
                        "  * Имеет адекватную обработку ошибок\n"
                        "  * Соответствует высоким стилевым стандартам\n"
                        "  * Предлагаемые доработки носят незначительный или рекомендательный характер\n\n"
                        "- [STATUS: PARTIAL] - если код в основном готов, но требует доработок:\n"
                        "  * Реализована основная функциональность\n"
                        "  * Есть заметные недочеты (например, отсутствие обработки некоторых ошибок, неоптимальный код)\n"
                        "  * Требуются улучшения для повышения качества/надежности\n\n"
                        "- [STATUS: INCOMPLETE] - если код требует серьезных доработок:\n"
                        "  * Есть явные недоработки (TODO, заглушки, незавершенные методы/классы)\n"
                        "  * Критические ошибки в логике или архитектуре\n"
                        "  * Отсутствует или неадекватная обработка ошибок\n"
                        "  * Серьезные проблемы с качеством или безопасностью\n\n"
                        "В самом начале ответа укажи статус файла в формате: [STATUS: COMPLETED], [STATUS: PARTIAL] или [STATUS: INCOMPLETE]. Без лишних слов перед статусом.\n"
                        "Затем дай развернутый, структурированный анализ по пунктам 1-5, приводя конкретные примеры из кода (указывая строки, если возможно)."
            },
            {
                "role": "user",
                "text": f"Проанализируй код из файла '{filename}' (автор: {author_email}):\n\n```\n{truncated_code}\n```"
            }
        ]

        try:
            result = self.sdk.models.completions("yandexgpt").configure(temperature=0.2, max_tokens=1500).run(messages)
            logger.info(f"Анализ файла {filename} завершен.")
            return result
        except Exception as e:
            logger.error(f"Ошибка вызова YandexGPT API для файла {filename}: {e}", exc_info=True)
            return []

    def make_general_analysis(self):
        if not self.summaries:
            logger.warning("Нет данных для общего анализа.")
            return "Нет данных для общего анализа."

        MAX_SUMMARY_LEN = 5500
        combined_summary = "\n".join([
            f"Файл: {item['filename']}\nАвтор: {item['author']}\nСтатус: {item['status']}\nКраткий анализ: {item['summary']}\n---"
            for item in self.summaries
        ])
        truncated_summary = combined_summary[:MAX_SUMMARY_LEN]
        if len(combined_summary) > MAX_SUMMARY_LEN:
             logger.warning(f"Объединенное резюме для общего анализа обрезано до {MAX_SUMMARY_LEN} символов.")

        total_files_safe = self.total_files if self.total_files > 0 else 1
        task_weight = 100 / total_files_safe
        completion_percentage = (self.completed_files + self.partial_files * 0.5) / total_files_safe * 100

        messages = [
            {
                "role": "system",
                "text": "Ты - опытный технический лидер (Team Lead/Architect). На основании предоставленных кратких анализов отдельных файлов, сделай **обобщенный** и **высокоуровневый** анализ всей кодовой базы (или ее части, представленной файлами). Твоя цель - дать общую картину и стратегические рекомендации.\n\n"
                      "**Структура отчета:**\n\n"
                      "1.  **Сводка**\n"
                      "    *   Email авторов: [Перечислить всех уникальных авторов]\n"
                      "    *   Проанализировано файлов: {total_files}\n"
                      "    *   Общий прогресс (оценка): {completion_percentage:.1f}% (COMPLETED=100%, PARTIAL=50%)\n\n"
                      "2.  **Общая оценка качества кода (1-10)**\n"
                      "    *   [Дай оценку от 1 до 10]\n"
                      "    *   **Обоснование:** [Подробно обоснуй оценку (4-6 предложений). Ссылайся на *общие тенденции*, замеченные в анализах файлов (например, 'часто встречается отсутствие...', 'в нескольких файлах отмечено хорошее...'). Не углубляйся в детали конкретных файлов здесь.]\n\n"
                      "3.  **Предполагаемая сложность поддержки**\n"
                      "    *   [Оцени сложность: Высокая/Средняя/Низкая]\n"
                      "    *   **Обоснование:** [Объясни (3-5 предложений), почему ты так считаешь, основываясь на общих характеристиках кода: связанность, понятность, наличие тестов (если упоминалось), повторяющийся код и т.д.]\n\n"
                      "4.  **Ключевые выявленные проблемы и риски**\n"
                      "    *   [Опиши 2-4 *основные* повторяющиеся или наиболее критичные проблемы, замеченные в анализах (например, 'Недостаточная обработка ошибок', 'Потенциальные уязвимости XSS', 'Сложная логика в контроллерах'). (6-8 предложений на весь пункт)]\n"
                      "    *   **Возможные последствия:** [Кратко опиши риски, связанные с этими проблемами ( нестабильность, уязвимости, трудности развития).]\n\n"
                      "5.  **Замеченные антипаттерны (если есть)**\n"
                      "    *   [Перечисли 1-3 *наиболее часто* встречающихся антипаттерна, если они были явно видны в анализах (например, 'God Object', 'Spaghetti Code', 'Magic Numbers'). Если нет явных - напиши 'Явных распространенных антипаттернов не выявлено'. (5-7 предложений на весь пункт)]\n"
                      "    *   **Рекомендации по рефакторингу:** [Предложи общие подходы к их устранению.]\n\n"
                      "6.  **Позитивные моменты и сильные стороны**\n"
                      "    *   [Отметь 1-3 *общих* положительных аспекта, если они есть (например, 'Хорошее покрытие тестами в модуле X', 'Единообразный стиль кода', 'Четкое разделение ответственности в Y'). Если нет - 'Значимых позитивных моментов не выявлено'. (5-7 предложений на весь пункт)]\n"
                      "    *   **Как развить:** [Краткие идеи по масштабированию хороших практик.]\n\n"
                      "7.  **Стратегические рекомендации по улучшению**\n"
                      "    *   [Дай 3-5 *высокоуровневых* рекомендаций для улучшения кодовой базы в целом. Фокусируйся на наиболее важных аспектах. (например, 'Внедрить статический анализ', 'Провести ревью безопасности', 'Улучшить логирование', 'Рефакторинг модуля Z'). Укажи примерный приоритет (Высокий/Средний/Низкий). (6-8 предложений на весь пункт)]\n\n"
                      "**Форматирование:**\n"
                      "- Используй **жирный шрифт** для заголовков и подзаголовков.\n"
                      "- Используй маркеры (*) для списков.\n"
                      "- Будь конкретным, но избегай излишней детализации по отдельным файлам. Сосредоточься на общей картине."
                .format(
                    total_files=self.total_files,
                    completion_percentage=completion_percentage
                )
            },
            {
                "role": "user",
                "text": f"Вот краткие анализы файлов:\n\n{truncated_summary}\n\nСделай общий вывод и дай стратегические рекомендации."
            }
        ]

        try:
            result = self.sdk.models.completions("yandexgpt").configure(temperature=0.3, max_tokens=2000).run(messages)
            logger.info("Общий анализ кодовой базы завершен.")
            return result[0].text if result and result[0] else "Не удалось сгенерировать общий анализ."
        except Exception as e:
            logger.error(f"Ошибка вызова YandexGPT API для общего анализа: {e}", exc_info=True)
            return f"Ошибка при генерации общего анализа: {e}"

    def process_json_and_generate_pdf(self, input_json_path: str, output_pdf_path: str) -> str:
        logger.info(f"Начало обработки LLM для JSON: {input_json_path}")
        self.analysis_results = []
        self.summaries = []
        self.authors_stats = defaultdict(list)
        self.total_files = 0
        self.completed_files = 0
        self.partial_files = 0
        self.incomplete_files = 0

        try:
            with open(input_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            logger.error(f"Ошибка: JSON файл не найден: {input_json_path}")
            raise
        except json.JSONDecodeError as e:
             logger.error(f"Ошибка декодирования JSON файла {input_json_path}: {e}")
             raise ValueError(f"Некорректный формат JSON файла: {input_json_path}") from e
        except Exception as e:
             logger.error(f"Не удалось прочитать JSON файл {input_json_path}: {e}")
             raise

        if "files" not in data or not isinstance(data["files"], list):
             logger.error(f"Некорректная структура JSON: отсутствует ключ 'files' или он не является списком в {input_json_path}")
             raise ValueError(f"Некорректная структура JSON в {input_json_path}")

        self.total_files = len(data["files"])
        if self.total_files == 0:
            logger.warning(f"В JSON файле {input_json_path} нет файлов для анализа.")
            report_content = "В предоставленном JSON отчете не найдено файлов для анализа."
            report_title = f"Анализ кодовой базы (Файлы не найдены)"
            PDFGenerator.save_to_pdf(output_pdf_path, report_title, report_content)
            logger.info(f"Пустой отчет PDF сохранен: {output_pdf_path}, так как файлы не найдены.")
            return output_pdf_path


        logger.info(f"Начинаем анализ {self.total_files} файлов из {input_json_path}...")
        files_to_process = data["files"]

        for i, file_data in enumerate(files_to_process, 1):
            filename = file_data.get('filename')
            author_email = file_data.get('author_email')
            code = file_data.get('code')

            if not all([filename, author_email, code]):
                logger.warning(f"Пропуск файла {i}/{self.total_files}: отсутствуют необходимые данные (filename, author_email, code). Данные: {file_data.keys()}")
                continue

            logger.info(f"[{i}/{self.total_files}] Анализ файла: {filename} (Автор: {author_email})")

            try:
                code_str = str(code) if not isinstance(code, str) else code
                analysis_result = self.analyze_code(code_str, filename, author_email)

                if analysis_result and analysis_result[0]:
                    alternative = analysis_result[0]
                    raw_text = alternative.text
                    logger.debug(f"Результат анализа для {filename}:\n{raw_text[:300]}...")

                    status = "INCOMPLETE"
                    text_upper = raw_text.upper()
                    if text_upper.startswith("[STATUS: COMPLETED]"):
                         status = "COMPLETED"
                         self.completed_files += 1
                    elif text_upper.startswith("[STATUS: PARTIAL]"):
                         status = "PARTIAL"
                         self.partial_files += 1
                    else:
                        if text_upper.startswith("[STATUS: INCOMPLETE]"):
                             status = "INCOMPLETE"
                        self.incomplete_files += 1

                    summary_text = raw_text
                    if summary_text.startswith("[STATUS:"):
                        end_bracket_index = summary_text.find("]")
                        if end_bracket_index != -1:
                            summary_text = summary_text[end_bracket_index+1:].strip()

                    self.summaries.append({
                        "filename": filename,
                        "author": author_email,
                        "status": status,
                        "summary": summary_text[:700]
                    })

                    self.authors_stats[author_email].append({
                        "filename": filename,
                        "status": status
                    })
                else:
                    logger.warning(f"Не получен результат анализа от LLM для файла {filename}. Пропуск.")
                    self.summaries.append({
                        "filename": filename,
                        "author": author_email,
                        "status": "FAILED_ANALYSIS",
                        "summary": "[Анализ не удался или не вернул результат]"
                    })
                    self.incomplete_files += 1
            except Exception as file_analysis_err:
                logger.error(f"Ошибка при обработке файла {filename}: {file_analysis_err}", exc_info=True)
                self.summaries.append({
                    "filename": filename,
                    "author": author_email,
                    "status": "ERROR",
                    "summary": f"[Ошибка обработки файла: {file_analysis_err}]"
                })
                self.incomplete_files += 1


        logger.info("\n=== Генерация общего анализа кодовой базы ===")
        try:
            general_analysis_text = self.make_general_analysis()
            logger.debug(f"Общий анализ (начало):\n{general_analysis_text[:300]}...")
        except Exception as general_analysis_err:
             logger.error(f"Критическая ошибка при генерации общего анализа: {general_analysis_err}", exc_info=True)
             general_analysis_text = f"\n\n!! Ошибка при генерации общего отчета: {general_analysis_err} !!"

        report_content = general_analysis_text

        total_files_safe = self.total_files if self.total_files > 0 else 1
        task_weight = 100 / total_files_safe
        completion_percentage = (self.completed_files + self.partial_files * 0.5) / total_files_safe * 100

        stats_content = "\n\n\n=== ДЕТАЛЬНАЯ СТАТИСТИКА ПО ФАЙЛАМ ===\n"
        stats_content += f"Общее количество файлов для анализа: {self.total_files}\n"
        stats_content += f"Завершено полностью (COMPLETED): {self.completed_files}\n"
        stats_content += f"Завершено частично (PARTIAL): {self.partial_files}\n"
        stats_content += f"Требует доработки (INCOMPLETE/ERROR/FAILED): {self.incomplete_files}\n"
        stats_content += f"Общий процент выполнения (оценка): {completion_percentage:.1f}%\n"

        stats_content += "\nСтатистика по авторам:\n"
        if self.authors_stats:
            for author, files in self.authors_stats.items():
                author_total = len(files)
                if author_total > 0:
                    author_completed = sum(1 for f in files if f["status"] == "COMPLETED")
                    author_partial = sum(1 for f in files if f["status"] == "PARTIAL")
                    author_incomplete = author_total - author_completed - author_partial
                    author_percentage = (author_completed + author_partial * 0.5) / author_total * 100
                    stats_content += (f"\n- **{author}** ({author_total} файлов):\n"
                                    f"  Завершено: {author_completed}\n"
                                    f"  Частично: {author_partial}\n"
                                    f"  Не завершено/Ошибки: {author_incomplete}\n"
                                    f"  Процент выполнения (оценка): {author_percentage:.1f}%\n")
        else:
            stats_content += "Нет данных по авторам.\n"

        report_content += stats_content

        report_content += "\n\n\n=== РЕЗУЛЬТАТЫ АНАЛИЗА ОТДЕЛЬНЫХ ФАЙЛОВ ===\n"
        if self.summaries:
             for item in self.summaries:
                 report_content += f"\n**Файл:** {item['filename']}\n"
                 report_content += f"**Автор:** {item['author']}\n"
                 report_content += f"**Статус:** {item['status']}\n"
                 report_content += f"**Краткий анализ:**\n{item['summary']}\n"
                 report_content += "---\n"
        else:
             report_content += "Нет результатов анализа отдельных файлов.\n"

        report_title = f"Анализ кодовой базы (Отчет {datetime.now().strftime('%Y-%m-%d')})"
        try:
            PDFGenerator.save_to_pdf(output_pdf_path, report_title, report_content)
            logger.info(f"Итоговый PDF отчет сохранен: {output_pdf_path}")
            return output_pdf_path
        except Exception as pdf_err:
             logger.error(f"Не удалось сохранить итоговый PDF отчет {output_pdf_path}: {pdf_err}", exc_info=True)
             raise