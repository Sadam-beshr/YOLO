# =================================================================
# app.py النهائي لمشروع ترجمة لغة الإشارة
# مصمم للعمل مع خادم الإنتاج Gunicorn
# =================================================================

import os
import uuid
from flask import Flask, request, jsonify, url_for
from flask_cors import CORS
from ultralytics import YOLO
from gtts import gTTS
from PIL import Image

# --- 1. تهيئة التطبيق وإعداد CORS ---
app = Flask(__name__)
CORS(app)
print("✅ Flask App and CORS initialized.")

# --- 2. إعداد مجلدات الرفع ---
# سيتم استخدام هذا المجلد لحفظ ملفات الصوت التي يتم إنشاؤها
UPLOAD_FOLDER = 'static/audio'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
print(f"✅ Static folder configured at: {UPLOAD_FOLDER}")

# --- 3. تحميل النموذج وقاموس الترجمة عند بدء التشغيل ---
# يتم هذا مرة واحدة فقط بفضل خيار --preload في Gunicorn
try:
    print("⏳ [Step 1/5] Loading YOLO model...")
    model = YOLO('best.pt')
    print("✅ [Step 1/5] Model loaded successfully.")
except Exception as e:
    # إذا فشل تحميل النموذج، سيتوقف التطبيق عن العمل هنا
    # وسنرى هذا الخطأ في سجلات EasyPanel
    print(f"❌ CRITICAL: Failed to load model. Error: {e}")

# قاموس لترجمة أسماء الفئات من الإنجليزية إلى العربية
TRANSLATION_DICT = {
    "alif": "أ", "baa": "ب", "taa": "ت", "thaa": "ث", "jeem": "ج",
    "haa": "ح", "khaa": "خ", "dal": "د", "thal": "ذ", "raa": "ر",
    "zay": "ز", "seen": "س", "sheen": "ش", "saad": "ص", "daad": "ض",
    "tah": "ط", "zah": "ظ", "ain": "ع", "ghain": "غ", "faa": "ف",
    "qaaf": "ق", "kaaf": "ك", "laam": "ل", "meem": "م", "noon": "ن",
    "heh": "ه", "waw": "و", "yaa": "ي"
}
print("✅ Translation dictionary loaded.")


# --- 4. نقطة نهاية لفحص الصحة (ممارسة جيدة) ---
# يمكن استخدامها لمراقبة ما إذا كان التطبيق لا يزال يعمل
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200


# --- 5. نقطة النهاية الرئيسية لمعالجة الصور ---
@app.route('/predict', methods=['POST'])
def predict():
    print("\n--- Received a new request for /predict ---")

    # التحقق من أن الطلب يحتوي على ملف صورة
    if 'image' not in request.files:
        print("❌ [Step 2/5] Failed: No image file in request.")
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        print("❌ [Step 2/5] Failed: No image selected.")
        return jsonify({'error': 'No image selected'}), 400
    
    print("✅ [Step 2/5] Image file received successfully.")

    try:
        # فتح الصورة وتشغيل نموذج YOLO عليها
        print("⏳ [Step 3/5] Running model inference...")
        image = Image.open(file.stream)
        results = model(image, conf=0.25) # يمكن تعديل درجة الثقة هنا
        result = results[0]
        print("✅ [Step 3/5] Model inference completed.")

        # معالجة النتائج
        if len(result.boxes) == 0:
            print("ℹ️ [Step 4/5] No objects detected. Responding.")
            return jsonify({'character': 'لم يتم التعرف على حرف', 'audio_url': None, 'confidence': 0})

        # الحصول على أفضل نتيجة
        best_box = result.boxes[0]
        class_id = int(best_box.cls[0])
        original_class_name = model.names[class_id]
        confidence = float(best_box.conf[0])
        print(f"✅ [Step 4/5] Object detected: {original_class_name} with confidence {confidence:.2f}")

        # ترجمة اسم الفئة وتوليد ملف الصوت
        print("⏳ [Step 5/5] Generating audio...")
        translated_char = TRANSLATION_DICT.get(original_class_name, original_class_name)
        
        # إنشاء اسم ملف فريد لتجنب الكتابة فوق الملفات
        audio_filename = f"{uuid.uuid4()}.mp3"
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
        
        tts = gTTS(text=translated_char, lang='ar')
        tts.save(audio_path)

        # إنشاء رابط كامل لملف الصوت
        audio_url = url_for('static', filename=f'audio/{audio_filename}', _external=True)
        print(f"✅ [Step 5/5] Audio generated: {audio_url}")

        # إرجاع النتيجة النهائية كـ JSON
        print("🎉 --- Responding with successful result ---")
        return jsonify({
            'character': translated_char,
            'confidence': round(confidence, 2),
            'audio_url': audio_url
        })

    except Exception as e:
        # في حالة حدوث أي خطأ غير متوقع أثناء المعالجة
        print(f"❌ CRITICAL ERROR during processing: {str(e)}")
        return jsonify({'error': f'An error occurred during processing: {str(e)}'}), 500

# لا يوجد شيء هنا!
# تم حذف كتلة "if __name__ == '__main__':" لأن Gunicorn هو المسؤول عن تشغيل التطبيق.
