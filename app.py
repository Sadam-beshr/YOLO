# ... (كل الكود في الأعلى يبقى كما هو) ...

# --- تعريف نقطة النهاية (Endpoint) للـ API ---
@app.route('/predict', methods=['POST'])
def predict():
    # =================================================================
    #  !!! كود التشخيص المؤقت !!!
    # سنقوم بإرجاع ناتج وهمي فوراً لاختبار الاتصال والذاكرة
    # إذا نجح هذا، فالمشكلة 100% في استهلاك الذاكرة أثناء المعالجة
    
    # إنشاء ملف صوتي وهمي
    try:
        translated_char = "اختبار"
        audio_filename = "test.mp3"
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
        
        tts = gTTS(text=translated_char, lang='ar')
        tts.save(audio_path)
        audio_url = url_for('static', filename=f'audio/{audio_filename}', _external=True)

        print("✅ Responding with MOCK data successfully.") # رسالة لنراها في السجلات

        return jsonify({
            'character': 'نجح الاختبار',
            'confidence': 0.99,
            'audio_url': audio_url
        })
    except Exception as e:
        # إذا فشل حتى هذا الجزء البسيط، فالمشكلة أكبر
        print(f"❌ Mock data response failed: {str(e)}")
        return jsonify({'error': f'Mock data error: {str(e)}'}), 500
    # =================================================================


    # الكود الأصلي (سيتم تجاهله مؤقتاً بسبب return أعلاه)
    if 'image' not in request.files:
        # ... (باقي الكود الأصلي) ...
