import os
from flask import Flask, request, jsonify, url_for
from flask_cors import CORS
from ultralytics import YOLO
from gtts import gTTS
from PIL import Image
import uuid

# --- تهيئة التطبيق ---
app = Flask(__name__)
CORS(app)
print("✅ Flask App and CORS initialized.")

# --- إعداد المجلدات ---
UPLOAD_FOLDER = 'static/audio'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
print(f"✅ Static folder configured at: {UPLOAD_FOLDER}")

# --- تحميل النموذج وقاموس الترجمة ---
try:
    print("⏳ [Step 1/5] Loading YOLO model...")
    model = YOLO('best.pt')
    print("✅ [Step 1/5] Model loaded successfully.")
except Exception as e:
    print(f"❌ CRITICAL: Failed to load model. Error: {e}")

TRANSLATION_DICT = {
    "alif": "أ", "baa": "ب", "taa": "ت", "thaa": "ث", "jeem": "ج",
    "haa": "ح", "khaa": "خ", "dal": "د", "thal": "ذ", "raa": "ر",
    "zay": "ز", "seen": "س", "sheen": "ش", "saad": "ص", "daad": "ض",
    "tah": "ط", "zah": "ظ", "ain": "ع", "ghain": "غ", "faa": "ف",
    "qaaf": "ق", "kaaf": "ك", "laam": "ل", "meem": "م", "noon": "ن",
    "heh": "ه", "waw": "و", "yaa": "ي"
}

# --- نقطة نهاية فحص الصحة (مفيدة دائماً) ---
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200

# --- نقطة النهاية الرئيسية للمعالجة ---
@app.route('/predict', methods=['POST'])
def predict():
    print("\n--- Received a new request for /predict ---")

    # 1. التحقق من وجود الملف
    if 'image' not in request.files:
        print("❌ [Step 2/5] Failed: No image file in request.")
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        print("❌ [Step 2/5] Failed: No image selected.")
        return jsonify({'error': 'No image selected'}), 400
    
    print("✅ [Step 2/5] Image file received successfully.")

    try:
        # 2. تشغيل الاستدلال
        print("⏳ [Step 3/5] Running model inference...")
        image = Image.open(file.stream)
        results = model(image, conf=0.25)
        result = results[0]
        print("✅ [Step 3/5] Model inference completed.")

        # 3. معالجة النتائج
        if len(result.boxes) == 0:
            print("ℹ️ [Step 4/5] No objects detected. Responding.")
            return jsonify({'character': 'لم يتم التعرف على حرف', 'audio_url': None, 'confidence': 0})

        best_box = result.boxes[0]
        class_id = int(best_box.cls[0])
        original_class_name = model.names[class_id]
        confidence = float(best_box.conf[0])
        print(f"✅ [Step 4/5] Object detected: {original_class_name} with confidence {confidence:.2f}")

        # 4. الترجمة وتوليد الصوت
        print("⏳ [Step 5/5] Generating audio...")
        translated_char = TRANSLATION_DICT.get(original_class_name, original_class_name)
        
        audio_filename = f"{uuid.uuid4()}.mp3"
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
        
        tts = gTTS(text=translated_char, lang='ar')
        tts.save(audio_path)

        audio_url = url_for('static', filename=f'audio/{audio_filename}', _external=True)
        print(f"✅ [Step 5/5] Audio generated: {audio_url}")

        # 5. إرجاع النتيجة النهائية
        print("🎉 --- Responding with successful result ---")
        return jsonify({
            'character': translated_char,
            'confidence': round(confidence, 2),
            'audio_url': audio_url
        })

    except Exception as e:
        # هذا الجزء مهم جداً لمعرفة أي خطأ يحدث أثناء المعالجة
        print(f"❌ CRITICAL ERROR during processing: {str(e)}")
        return jsonify({'error': f'An error occurred during processing: {str(e)}'}), 500

# --- تشغيل التطبيق ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
