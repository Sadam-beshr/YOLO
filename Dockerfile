# =================================================================
# Dockerfile - نسخة مستقرة تعمل مباشرة مع Python
# =================================================================

# 1. استخدام صورة Python رسمية كأساس
FROM python:3.9-slim

# 2. إضافة حجة بناء لإبطال ذاكرة التخزين المؤقت
ARG CACHE_BUSTER=1

# 3. إعداد متغير بيئة
ENV DEBIAN_FRONTEND=noninteractive

# 4. تحديد مجلد العمل
WORKDIR /app

# 5. تثبيت اعتماديات نظام التشغيل
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 6. نسخ وتثبيت متطلبات Python
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=1000 -r requirements.txt

# 7. إبطال ذاكرة التخزين المؤقت ونسخ باقي الملفات
RUN echo "Cache buster value: $CACHE_BUSTER"
COPY . .

# 8. تحديد المنفذ الذي سيعمل عليه التطبيق
EXPOSE 8000

# 9. الأمر النهائي لتشغيل التطبيق مباشرة (بدون Gunicorn)
CMD ["python", "app.py"]
