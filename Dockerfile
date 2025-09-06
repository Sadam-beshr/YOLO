# 1. استخدام صورة Python رسمية كأساس
FROM python:3.9-slim

# 2. إعداد متغير بيئة لمنع apt من طلب إدخال تفاعلي
ENV DEBIAN_FRONTEND=noninteractive

# 3. تحديد مجلد العمل داخل الحاوية
WORKDIR /app

# 4. تثبيت جميع اعتماديات نظام التشغيل التي تحتاجها OpenCV و gTTS
# هذه هي القائمة الشاملة لحل جميع مشاكل "cannot open shared object file"
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 5. نسخ ملف المتطلبات
COPY requirements.txt .

# 6. تثبيت مكتبات Python
RUN pip install --no-cache-dir --timeout=1000 -r requirements.txt

# 7. نسخ باقي ملفات المشروع
COPY . .

# 8. تحديد المنفذ الذي سيعمل عليه التطبيق داخل الحاوية
# 8. تحديد المنفذ الذي سيعمل عليه التطبيق داخل الحاوية
EXPOSE 8000

# 9. الأمر الذي سيتم تشغيله عند بدء تشغيل الحاوية
# ... (كل الأسطر السابقة تبقى كما هي) ...

# 9. الأمر الذي سيتم تشغيله عند بدء تشغيل الحاوية
# أضفنا --preload لتحميل التطبيق قبل إنشاء العمال
# وأبقينا على --timeout لضمان معالجة الطلبات الطويلة
#CMD ["gunicorn", "--workers", "1", "--bind", "0.0.0.0:5000", "--timeout", "300", "--preload", "app:app"]

# 9. الأمر الذي سيتم تشغيله عند بدء تشغيل الحاوية
CMD ["python", "app.py"]

