# Используем базовый образ с Python 3.8-slim
FROM python:3.8-slim

# Устанавливаем зависимости
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Копируем содержимое корневой папки проекта в контейнер
COPY . /app

# Указываем рабочую директорию
WORKDIR /app/UInt

# Указываем порт
EXPOSE 5002

# Запуск Flask-приложения
CMD ["flask", "run", "--host=0.0.0.0"]