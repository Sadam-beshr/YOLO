# =================================================================
# app.py - نسخة مستقرة تعمل مباشرة مع Python
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
UPLOAD_FOLDER = 'static/audio'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
print(f"✅ Static folder configured at: {UPLOAD_FOLDER}")

# --- 3. تحميل النموذج وقاموس الترجمة ---
try:
    print("⏳ Loading YOLO model...")
    model = YOLO('best.pt')
    print("✅ Model loaded successfully.")
except Exception as e:
    print(f"❌ CRITICAL: Failed to load model. Error: {e}")

# قاموس لترجمة أسماء الفئات
TRANSLATION_DICT = {
    "alif": "أ", "baa": "ب", "taa": "ت", "thaa": "ث", "jeem": "ج",
    "haa": "ح", "khaa": "خ", "dal": "د", "thal": "ذ", "raa": "ر",
    "zay": "ز", "seen": "س", "sheen": "ش", "saad": "ص", "daad": "ض",
    "tah": "ط", "zah": "ظ", "ain": "ع", "ghain": "غ", "faa": "ف",
    "qaaf": "ق", "kaaf": "ك", "laam": "ل", "meem": "م", "noon": "ن",
    "heh": "ه", "waw": "و", "yaa": "ي"
}
print("✅ Translation dictionary loaded.")

# --- 4. نقطة نهاية لفحص الصحة ---
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200

# --- 5. نقطة النهاية الرئيسية للمعالجة ---
@app.route('/predict', methods=['POST'])
def predict():
    # ... (كود المعالجة يبقى كما هو) ...
    print("\n--- Received a new request for /predict ---")
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400
    try:
        image = Image.open(file.stream)
        results = model(image, conf=0.25)
        result = results[0]
        if len(result.boxes) == 0:
            return jsonify({'character': 'لم يتم التعرف على حرف', 'audio_url': None, 'confidence': 0})
        best_box = result.boxes[0]
        class_id = int(best_box.cls[0])
        original_class_name = model.names[class_id]
        confidence = float(best_box.conf[0])
        translated_char = TRANSLATION_DICT.get(original_class_name, original_class_name)
        audio_filename = f"{uuid.uuid4()}.mp3"
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
        tts = gTTS(text=translated_char, lang='ar')
        tts.save(audio_path)
        audio_url = url_for('static', filename=f'audio/{audio_filename}', _external=True)
        return jsonify({
            'character': translated_char,
            'confidence': round(confidence, 2),
            'audio_url': audio_url
        })
    except Exception as e:
        return jsonify({'error': f'An error occurred during processing: {str(e)}'}), 500

# --- 6. تشغيل الخادم مباشرة (هذا هو الجزء الذي أعدناه) ---
# هذا الكود يجعل الملف قابلاً للتشغيل ومستقلاً
if __name__ == '__main__':
    # قراءة المنفذ من متغيرات البيئة أو استخدام 8000 كافتراضي
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
