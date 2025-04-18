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
                "text": "Ты - опытный разработчик. Проанализируй код по критериям:\n"
                        "1. Качество кода\n2. Потенциальные проблемы\n3. Возможности улучшения\n\n"
                        "Определи статус файла по следующим правилам:\n"
                        "- [STATUS: COMPLETED] - если код полностью готов и соответствует стандартам:\n"
                        "  * Реализует всю заявленную функциональность\n"
                        "  * Имеет базовую обработку ошибок\n"
                        "  * Соответствует стилевым стандартам\n"
                        "  * Доработки носят рекомендательный характер\n\n"
                        "- [STATUS: PARTIAL] - если код в основном готов, но требует доработок:\n"
                        "  * Реализована основная функциональность\n"
                        "  * Есть небольшие недочеты\n"
                        "  * Требуются незначительные улучшения\n\n"
                        "- [STATUS: INCOMPLETE] - если код требует серьезных доработок:\n"
                        "  * Есть явные недоработки (TODO, незавершенные методы)\n"
                        "  * Критические ошибки в логике\n"
                        "  * Отсутствует обработка ошибок\n\n"
                        "В начале ответа укажи статус файла в формате: [STATUS: COMPLETED], [STATUS: PARTIAL] или [STATUS: INCOMPLETE]\n"
                        "Затем дай развернутый анализ."
            },
            {
                "role": "user",
                "text": f"Проанализируй код из {filename}:\n\n{code[:3000]}"
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
                "text": "Ты - технический лидер. На основании этих анализов дай общую оценку по следующим пунктам:\n\n"
                      "1. Email автора\n"
                      "• Перечисли все email авторов из анализов\n\n"
                      "2. Количество задач\n"
                      "• Укажи только число: {total_files}\n\n"
                      "3. Общая оценка кода по десятибальной шкале\n"
                      "• Дай оценку от 1 до 10\n"
                      "• Подробно обоснуй оценку, ссылаясь на конкретные примеры из кода\n\n"
                      "4. Процент выполнения\n"
                      "• Укажи процент выполнения: {completion_percentage:.2f}%\n"
                      "• (Учитывается 100% для COMPLETED и 50% для PARTIAL)\n\n"
                      "5. Сложность кода\n"
                      "• Оцени сложность (Сложная/Средняя/Низкая)\n"
                      "• Приведи конкретные примеры, обосновывающие твою оценку\n\n"
                      "6. Выявленные проблемы\n"
                      "• Перечисли все найденные проблемы\n"
                      "• По каждой проблеме приведи:\n"
                      "  - Конкретный пример из кода (файл и строка если возможно)\n"
                      "  - Описание проблемы\n"
                      "  - Последствия проблемы\n\n"
                      "7. Выявленные антипаттерны\n"
                      "• Перечисли все найденные антипаттерны\n"
                      "• По каждому приведи:\n"
                      "  - Конкретный пример из кода\n"
                      "  - Описание почему это антипаттерн\n"
                      "  - Как можно исправить\n\n"
                      "8. Выявленные позитивные моменты\n"
                      "• Перечисли все хорошие практики\n"
                      "• По каждой приведи:\n"
                      "  - Конкретный пример из кода\n"
                      "  - Описание почему это хорошая практика\n"
                      "  - Как можно развить этот подход\n\n"
                      "9. Рекомендации по улучшению\n"
                      "• Дай конкретные рекомендации для каждого выявленного недостатка\n"
                      "• Укажи приоритеты исправления\n"
                      "• Предложи конкретные способы реализации улучшений\n\n"
                      "Форматирование:\n"
                      "- Каждый пункт начинается с новой строки\n"
                      "- Подпункты выделяются маркерами\n"
                      "- Примеры кода оформляются как цитаты\n"
                      "- Названия файлов выделяются жирным\n"
                      "- Используй четкие заголовки для каждого пункта\n"
                      "- Будь максимально конкретным, избегай общих фраз"
                .format(
                    total_files=self.total_files,
                    completion_percentage=completion_percentage
                )
            },
            {
                "role": "user",
                "text": f"Вот краткие анализы файлов:\n\n{combined_summary[:6000]}\n\n"
                        "Сделай общий вывод о кодовой базе, выявленные проблемы, выявленные антипаттерны, положительные моменты и рекоменадции должны быть на высоком уровне(минимум мидл), расписывай эти пункты на 6-8 предложений, обязателтно помечай заголовки пунктов:"
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

        report_title = f"Анализ кодовой базы (Отчет {datetime.now().strftime('%Y-%m-%d')})"
        try:
            PDFGenerator.save_to_pdf(output_pdf_path, report_title, report_content)
            logger.info(f"Итоговый PDF отчет сохранен: {output_pdf_path}")
            return output_pdf_path
        except Exception as pdf_err:
             logger.error(f"Не удалось сохранить итоговый PDF отчет {output_pdf_path}: {pdf_err}", exc_info=True)
             raise