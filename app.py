# =================================================================
# app.py - نسخة مستقرة مع إضافة ميزة "تعلم إشارة"
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
# هذا المجلد سيحتوي على مجلدات فرعية لملفات الصوت والصور المرجعية
UPLOAD_FOLDER = 'static' 
if not os.path.exists(os.path.join(UPLOAD_FOLDER, 'audio')):
    os.makedirs(os.path.join(UPLOAD_FOLDER, 'audio'))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
print(f"✅ Static folder configured at: {UPLOAD_FOLDER}")

# --- 3. تحميل النموذج وقواميس الترجمة ---
try:
    print("⏳ Loading YOLO model...")
    model = YOLO('best.pt')
    print("✅ Model loaded successfully.")
except Exception as e:
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

# قاموس عكسي لترجمة الحروف العربية إلى أسماء إنجليزية (للميزة الجديدة)
REVERSE_TRANSLATION_DICT = {v: k for k, v in TRANSLATION_DICT.items()}
print("✅ Reverse translation dictionary loaded.")


# --- 4. نقطة نهاية لفحص الصحة ---
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200


# --- 5. نقطة النهاية الرئيسية للمعالجة (التعرف على الإشارة) ---
@app.route('/predict', methods=['POST'])
def predict():
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
        
        # مسار حفظ ملفات الصوت
        audio_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'audio')
        audio_filename = f"{uuid.uuid4()}.mp3"
        audio_path = os.path.join(audio_folder, audio_filename)
        
        tts = gTTS(text=translated_char, lang='ar')
        tts.save(audio_path)
        
        # إنشاء رابط كامل لملف الصوت
        audio_url = url_for('static', filename=f'audio/{audio_filename}', _external=True)
        
        return jsonify({
            'character': translated_char,
            'confidence': round(confidence, 2),
            'audio_url': audio_url
        })
    except Exception as e:
        print(f"❌ CRITICAL ERROR during /predict: {str(e)}")
        return jsonify({'error': f'An error occurred during processing: {str(e)}'}), 500


# --- 6. نقطة نهاية جديدة لجلب صورة الإشارة (تعلم إشارة) ---
@app.route('/get_sign_image', methods=['POST'])
def get_sign_image():
    print("\n--- Received a new request for /get_sign_image ---")
    
    data = request.get_json()
    if not data or 'character' not in data:
        return jsonify({'error': 'Character not provided'}), 400

    char_ar = data['character']
    char_en = REVERSE_TRANSLATION_DICT.get(char_ar)

    if not char_en:
        print(f"❌ Invalid character received: {char_ar}")
        return jsonify({'error': 'Invalid character'}), 400

    # بناء المسار المتوقع للصورة داخل مجلد static
    image_path = f'reference_images/{char_en}.jpg'
    
    # التحقق من وجود الملف فعلياً
    if os.path.exists(os.path.join(app.static_folder, image_path)):
        # استخدام url_for لإنشاء رابط كامل وآمن للصورة
        image_url = url_for('static', filename=image_path, _external=True)
        print(f"✅ Found image for '{char_ar}'. Sending URL: {image_url}")
        return jsonify({'image_url': image_url})
    else:
        print(f"❌ Reference image not found for: {char_en}.jpg")
        return jsonify({'error': 'Reference image not found'}), 404


# --- 7. تشغيل الخادم مباشرة ---
# هذا الكود يجعل الملف قابلاً للتشغيل ومستقلاً
if __name__ == '__main__':
    # قراءة المنفذ من متغيرات البيئة أو استخدام 8000 كافتراضي
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
