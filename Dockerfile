# 1. استخدام صورة Python رسمية كأساس
FROM python:3.9-slim

# 2. تحديد مجلد العمل داخل الحاوية
WORKDIR /app

# 3. نسخ ملفات المشروع إلى الحاوية
COPY requirements.txt .

# 4. تثبيت اعتماديات نظام التشغيل التي تحتاجها OpenCV
# هذا هو السطر المُصحّح. نستخدم libgl1 بدلاً من libgl1-mesa-glx
RUN apt-get update && apt-get install -y libgl1

# 5. تثبيت مكتبات Python
# أضفت --timeout=1000 لزيادة وقت الانتظار أثناء تحميل المكتبات الكبيرة مثل torch
RUN pip install --no-cache-dir --timeout=1000 -r requirements.txt

# 6. نسخ باقي ملفات المشروع
COPY . .

# 7. تحديد المنفذ الذي سيعمل عليه التطبيق داخل الحاوية
EXPOSE 5000

# 8. الأمر الذي سيتم تشغيله عند بدء تشغيل الحاوية
CMD ["gunicorn", "--workers", "1", "--bind", "0.0.0.0:5000", "app:app"]
