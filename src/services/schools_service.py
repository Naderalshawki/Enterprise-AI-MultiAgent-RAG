import os
import requests

# قراءة رابط الـ API الخاص بالمدارس من ملف .env
SCHOOLS_API_URL = os.getenv("SCHOOLS_API_URL")

def fetch_schools_data():
    """
    دالة للاتصال بالـ API الخارجي وجلب بيانات المدارس
    """
    if not SCHOOLS_API_URL:
        return {"error": "رابط المدارس غير موجود في ملف .env"}

    try:
        # إرسال طلب GET لجلب البيانات
        response = requests.get(SCHOOLS_API_URL, timeout=10)
        
        # التحقق من نجاح الطلب
        if response.status_code == 200:
            return response.json() # إرجاع البيانات كـ JSON
        else:
            return {"error": f"فشل في جلب البيانات، كود الخطأ: {response.status_code}"}
            
    except Exception as e:
        return {"error": f"حدث خطأ أثناء الاتصال: {str(e)}"}