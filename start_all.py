# import subprocess
# import sys
# import time
# import os
# import signal

# def run_all_servers():
#     print("=" * 60)
#     print("🚀 بدء تشغيل منصة ذكاء الأعمال (AI BI Platform)")
#     print("=" * 60)

#     # 1. سيرفر زميلك (RAG) على بورت 8001
#     print("⏳ جاري تشغيل سيرفر RAG (زميلك)...")
#     rag_path = r"C:\Users\Owner\OneDrive\Desktop\LLM_AI\ai-rag-backend"
#     rag_cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8001"]
    
#     rag_process = subprocess.Popen(
#         rag_cmd, 
#         cwd=rag_path, 
#         stdout=subprocess.PIPE, 
#         stderr=subprocess.STDOUT,
#         text=True
#     )
#     time.sleep(2) # ننتظر شوية عشان السيرفر يقوم
#     print("✅ سيرفر RAG شغال على المنفذ 8001")

#     # 2. سيرفرك إنت (AI Core) على بورت 10000
#     print("⏳ جاري تشغيل سيرفر AI Core...")
#     ai_path = r"C:\Users\Owner\OneDrive\Desktop\LLM_AI"
#     ai_cmd = [sys.executable, "-m", "uvicorn", "src.main:app", "--host", "127.0.0.1", "--port", "10000", "--reload"]
    
#     ai_process = subprocess.Popen(
#         ai_cmd, 
#         cwd=ai_path,
#         stdout=subprocess.PIPE, 
#         stderr=subprocess.STDOUT,
#         text=True
#     )
#     time.sleep(2)
#     print("✅ سيرفر AI Core شغال على المنفذ 10000")

#     # 3. الواجهة (React) على بورت 5173
#     print("⏳ جاري تشغيل واجهة React...")
#     ui_path = r"C:\Users\Owner\ai-test-ui"
#     ui_cmd = ["npm", "run", "dev"]
    
#     # نستخدم shell=True عشان PowerShell يفتح النافذة ويشغل npm
#     ui_process = subprocess.Popen(
#         ui_cmd, 
#         cwd=ui_path, 
#         shell=True,
#         creationflags=subprocess.CREATE_NEW_CONSOLE # نفتح نافذة جديدة للواجهة
#     )
#     print("✅ واجهة React شغالة على المنفذ 5173")
    
#     print("\n" + "=" * 60)
#     print("🎉 كل السيرفرات تعمل الآن!")
#     print("👉 افتح المتصفح على: http://localhost:5173")
#     print("⚠️  لإيقاف الكل، اضغط Ctrl+C في هذه النافذة.")
#     print("=" * 60 + "\n")

#     try:
#         # خلي السكريبت شغال لحد ما المستخدم يدوس Ctrl+C
#         while True:
#             # مراقبة حالة السيرفرات
#             if rag_process.poll() is not None:
#                 print("⚠️ تحذير: سيرفر RAG (زميلك) توقف!")
#             if ai_process.poll() is not None:
#                 print("⚠️ تحذير: سيرفر AI Core توقف!")
#             time.sleep(5)
            
#     except KeyboardInterrupt:
#         print("\n🛑 جاري إيقاف جميع السيرفرات...")
#         try:
#             rag_process.terminate()
#             ai_process.terminate()
#             # للأسف ui_process في نافذة جديدة، بنقفله بـ taskkill
#             subprocess.call(['taskkill', '/F', '/T', '/PID', str(ui_process.pid)], shell=True)
#         except Exception as e:
#             print(f"خطأ أثناء الإغلاق: {e}")
#         print("✅ تم إيقاف كل شيء بنجاح.")

# if __name__ == "__main__":
#     run_all_servers()

import subprocess
import sys
import time
import os
import signal

def run_all_servers():
    print("=" * 60)
    print("🚀 بدء تشغيل منصة ذكاء الأعمال (AI BI Platform)")
    print("=" * 60)

    # ==========================================================
    # ملاحظة: تم تعطيل سيرفر RAG مؤقتاً لعرض المشروع غداً
    # ==========================================================
    # # 1. سيرفر زميلك (RAG) على بورت 8001
    # print("⏳ جاري تشغيل سيرفر RAG (زميلك)...")
    # rag_path = r"C:\Users\Owner\OneDrive\Desktop\LLM_AI\ai-rag-backend"
    # rag_cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8001"]
    # 
    # rag_process = subprocess.Popen(
    #     rag_cmd, 
    #     cwd=rag_path, 
    #     stdout=subprocess.PIPE, 
    #     stderr=subprocess.STDOUT,
    #     text=True
    # )
    # time.sleep(2)
    # print("✅ سيرفر RAG شغال على المنفذ 8001")
    # ==========================================================

    # 2. سيرفرك إنت (AI Core) على بورت 10000
    print("⏳ جاري تشغيل سيرفر AI Core...")
    ai_path = r"C:\Users\Owner\OneDrive\Desktop\LLM_AI"
    ai_cmd = [sys.executable, "-m", "uvicorn", "src.main:app", "--host", "127.0.0.1", "--port", "10000", "--reload"]
    
    ai_process = subprocess.Popen(
        ai_cmd, 
        cwd=ai_path,
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT,
        text=True
    )
    time.sleep(2)
    print("✅ سيرفر AI Core شغال على المنفذ 10000")

    # 3. الواجهة (React) على بورت 5173
    print("⏳ جاري تشغيل واجهة React...")
    ui_path = r"C:\Users\Owner\ai-test-ui"
    ui_cmd = ["npm", "run", "dev"]
    
    ui_process = subprocess.Popen(
        ui_cmd, 
        cwd=ui_path, 
        shell=True,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    print("✅ واجهة React شغالة على المنفذ 5173")
    
    print("\n" + "=" * 60)
    print("🎉 السيرفرات تعمل الآن!")
    print("👉 افتح المتصفح على: http://localhost:5173")
    print("⚠️  لإيقاف الكل، اضغط Ctrl+C في هذه النافذة.")
    print("=" * 60 + "\n")

    try:
        while True:
            if ai_process.poll() is not None:
                print("⚠️ تحذير: سيرفر AI Core توقف!")
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n🛑 جاري إيقاف جميع السيرفرات...")
        try:
            ai_process.terminate()
            subprocess.call(['taskkill', '/F', '/T', '/PID', str(ui_process.pid)], shell=True)
        except Exception as e:
            print(f"خطأ أثناء الإغلاق: {e}")
        print("✅ تم إيقاف كل شيء بنجاح.")

if __name__ == "__main__":
    run_all_servers()