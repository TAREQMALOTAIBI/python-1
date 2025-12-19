# اسم الملف: app.py

import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import google.generativeai as genai # <-- الخطوة 1: استيراد مكتبة Google

# --- 1. إعداد تطبيق Flask (لا تغيير) ---
app = Flask(__name__)
CORS(app)

# --- 2. محاكاة قاعدة البيانات (لا تغيير) ---
data = {
    'أرامكو': {
        2023: {'الإيرادات': 1800, 'صافي الربح': 400, 'إجمالي الأصول': 3000, 'إجمالي الخصوم': 1500, 'حقوق الملكية': 1500, 'الأصول المتداولة': 800, 'الخصوم المتداولة': 600},
    },
    'سابك': {
        2023: {'الإيرادات': 400, 'صافي الربح': 50, 'إجمالي الأصول': 800, 'إجمالي الخصوم': 400, 'حقوق الملكية': 400, 'الأصول المتداولة': 200, 'الخصوم المتداولة': 150},
    }
}
df = pd.DataFrame.from_dict({(i, j): data[i][j] 
                           for i in data.keys() 
                           for j in data[i].keys()},
                          orient='index')

def calculate_ratios(financial_data):
    ratios = {}
    ratios['هامش صافي الربح'] = round(financial_data['صافي الربح'] / financial_data['الإيرادات'], 2)
    ratios['النسبة الحالية'] = round(financial_data['الأصول المتداولة'] / financial_data['الخصوم المتداولة'], 2)
    ratios['الدين إلى حقوق الملكية'] = round(financial_data['إجمالي الخصوم'] / financial_data['حقوق الملكية'], 2)
    return ratios

# --- 3. إعداد الاتصال بـ Gemini API (باستخدام مكتبة Google) ---
# الخطوة 2: استخدام الطريقة الرسمية من Google
try:
    # قراءة المفتاح من متغيرات البيئة في Vercel
    api_key = os.getenv('GEMINI_API_KEY')
    if api_key:
        genai.configure(api_key=api_key)
        # إنشاء النموذج
        model = genai.GenerativeModel('gemini-pro')
    else:
        print("تحذير: متغير البيئة GEMINI_API_KEY غير موجود.")
        model = None
except Exception as e:
    print(f"خطأ في تهيئة نموذج Gemini: {e}")
    model = None

# --- 4. نقطة النهاية الخاصة بالتحليل (مع تعديل طريقة الاستدعاء) ---
@app.route('/analyze', methods=['POST'])
def analyze_company():
    # ... (الجزء الخاص باستلام الطلب وتحديد الشركة يبقى كما هو) ...
    request_data = request.get_json()
    user_query = request_data.get('query')

    if not user_query:
        return jsonify({"error": "الرجاء إدخال استعلام."}), 400

    clean_query = user_query.strip()
    company_name = None
    if 'رامكو' in clean_query or 'أرامكو' in clean_query:
        company_name = 'أرامكو'
    elif 'سابك' in clean_query:
        company_name = 'سابك'
    
    if not company_name:
        return jsonify({"analysis": "عفواً، لم أتمكن من تحديد الشركة المطلوبة في قاعدة البيانات. حالياً، قاعدة البيانات تحتوي فقط على (أرامكو، سابك)."})

    try:
        company_data = df.loc[(company_name, 2023)].to_dict()
        ratios = calculate_ratios(company_data)
        retrieved_info = f"البيانات المالية لـ{company_name} عام 2023: {company_data}. النسب المالية المحسوبة: {ratios}"

        # صياغة الـ Prompt (لا تغيير هنا، يبقى كما هو)
        prompt = f"""
        أنت "محلل مالي آلي" خبير في سوق الأسهم السعودي... (بقية الـ prompt كما هو)
        """

        if not model:
             raise Exception("لم يتم تهيئة نموذج Gemini بشكل صحيح.")

        # الخطوة 3: استدعاء Gemini API بالطريقة الرسمية
        response = model.generate_content(prompt)
        
        # استخراج النص من الرد وتنسيقه
        # مكتبة Google قد تضيف علامات Markdown، لذا سنقوم بإزالتها أو استبدالها
        analysis = response.text.replace('**', '<b>').replace('*', '')

        return jsonify({"analysis": analysis})

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return jsonify({"error": f"حدث خطأ أثناء معالجة طلبك: {str(e)}"}), 500
