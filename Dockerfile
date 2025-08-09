FROM python:3.11-slim

# Устанавливаем unrar и tar
RUN apt-get update && apt-get install -y unrar-free tar \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копируем зависимости и устанавливаем
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY main.py .

# Запускаем бота
CMD ["python", "main.py"]
