# 1. استخدام صورة Python رسمية كأساس
FROM python:3.9-slim

# 2. تحديد مجلد العمل داخل الحاوية
WORKDIR /app

# 3. نسخ ملفات المشروع إلى الحاوية
# أولاً، ننسخ ملف المتطلبات لتثبيت المكتبات
COPY requirements.txt .

# 4. تثبيت المكتبات
# --no-cache-dir لتقليل حجم الصورة
RUN apt-get update && apt-get install -y libgl1-mesa-glx

RUN pip install --no-cache-dir -r requirements.txt

# 5. نسخ باقي ملفات المشروع
COPY . .

# 6. تحديد المنفذ الذي سيعمل عليه التطبيق داخل الحاوية
EXPOSE 5000

# 7. الأمر الذي سيتم تشغيله عند بدء تشغيل الحاوية
# نستخدم gunicorn كخادم ويب للإنتاج بدلاً من خادم Flask المدمج
CMD ["gunicorn", "--workers", "1", "--bind", "0.0.0.0:5000", "app:app"]
