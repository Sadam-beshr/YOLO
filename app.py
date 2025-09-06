import os
from flask import Flask, request, jsonify, url_for
from ultralytics import YOLO
from gtts import gTTS
from PIL import Image
import uuid # لإنشاء أسماء ملفات فريدة

# --- تهيئة التطبيق ---
app = Flask(__name__)
# تحديد مجلد حفظ الملفات المؤقتة (الصوت)
app.config['UPLOAD_FOLDER'] = 'static/audio'
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# --- تحميل النموذج وقاموس الترجمة (يتم مرة واحدة عند بدء التشغيل) ---
print("⏳ Loading YOLO model...")
model = YOLO('best.pt')
print("✅ Model loaded successfully.")

TRANSLATION_DICT = {
    "alif": "أ", "baa": "ب", "taa": "ت", "thaa": "ث", "jeem": "ج",
    "haa": "ح", "khaa": "خ", "dal": "د", "thal": "ذ", "raa": "ر",
    "zay": "ز", "seen": "س", "sheen": "ش", "saad": "ص", "daad": "ض",
    "tah": "ط", "zah": "ظ", "ain": "ع", "ghain": "غ", "faa": "ف",
    "qaaf": "ق", "kaaf": "ك", "laam": "ل", "meem": "م", "noon": "ن",
    "heh": "ه", "waw": "و", "yaa": "ي"
}

# --- تعريف نقطة النهاية (Endpoint) للـ API ---
@app.route('/predict', methods=['POST'])
def predict():
    # 1. التحقق من وجود ملف صورة في الطلب
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400

    try:
        # 2. قراءة الصورة وتشغيل الاستدلال
        image = Image.open(file.stream)
        results = model(image, conf=0.25)
        result = results[0]

        # 3. معالجة النتائج
        if len(result.boxes) == 0:
            return jsonify({'character': 'لم يتم التعرف على حرف', 'audio_url': None, 'confidence': 0})

        # أخذ النتيجة الأعلى ثقة فقط
        best_box = result.boxes[0]
        class_id = int(best_box.cls[0])
        original_class_name = model.names[class_id]
        confidence = float(best_box.conf[0])

        # 4. الترجمة وتوليد الصوت
        translated_char = TRANSLATION_DICT.get(original_class_name, original_class_name)
        
        # إنشاء اسم فريد لملف الصوت لتجنب التضارب
        audio_filename = f"{uuid.uuid4()}.mp3"
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
        
        tts = gTTS(text=translated_char, lang='ar')
        tts.save(audio_path)

        # إنشاء رابط كامل لملف الصوت يمكن للعميل الوصول إليه
        audio_url = url_for('static', filename=f'audio/{audio_filename}', _external=True)

        # 5. إرجاع النتيجة كـ JSON
        return jsonify({
            'character': translated_char,
            'confidence': round(confidence, 2),
            'audio_url': audio_url
        })

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

# --- تشغيل التطبيق (للاختبار المحلي) ---
if __name__ == '__main__':
    # host='0.0.0.0' يجعله متاحاً على شبكتك المحلية
    app.run(host='0.0.0.0', port=5000, debug=True)
