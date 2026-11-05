import asyncio
import json
import os
from src.bootstrap import create_agent_service


async def main():
    # تأكد من مسح الذاكرة القديمة لبدء اختبار نظيف
    memory_file = "data/episodic_memory.json"
    if os.path.exists(memory_file):
        os.remove(memory_file)
        print("🗑️  تم مسح الذاكرة القديمة.\n")

    svc = create_agent_service()

    # ==========================================================
    # الاختبار 1: سؤال RAG (يحتوي على keywords → deterministic routing)
    # ==========================================================
    print("=" * 60)
    print("TEST 1: RAG Question (deterministic routing)")
    print("=" * 60)

    ctx1 = await svc.process_question('لخص لي محتوى الملف المرفوع', 'test-user')
    print(f'نجح؟ {ctx1.success}')
    print(f'كيف تم التخطيط؟ {ctx1.metadata.get("plan", {}).get("generated_by")}')
    print(f'استخدم الذاكرة؟ {ctx1.metadata.get("plan", {}).get("episodic_warnings_used", False)}')

    print()
    print("=" * 60)
    print("TEST 2: Same RAG Question (should use lesson)")
    print("=" * 60)

    ctx2 = await svc.process_question('لخص لي محتوى الملف المرفوع', 'test-user')
    print(f'نجح؟ {ctx2.success}')
    print(f'كيف تم التخطيط؟ {ctx2.metadata.get("plan", {}).get("generated_by")}')
    print(f'استخدم الذاكرة؟ {ctx2.metadata.get("plan", {}).get("episodic_warnings_used", False)}')

    print()
    print("=" * 60)
    print("TEST 3: Generic Question (no keywords → LLM path)")
    print("=" * 60)

    ctx3 = await svc.process_question('ما هو أفضل شيء في العالم؟', 'test-user')
    print(f'نجح؟ {ctx3.success}')
    print(f'كيف تم التخطيط؟ {ctx3.metadata.get("plan", {}).get("generated_by")}')
    print(f'استخدم الذاكرة؟ {ctx3.metadata.get("plan", {}).get("episodic_warnings_used", False)}')

    # ==========================================================
    # عرض ملف الذاكرة
    # ==========================================================
    print()
    print("=" * 60)
    print("EPISODIC MEMORY CONTENTS")
    print("=" * 60)

    if os.path.exists(memory_file):
        with open(memory_file, "r", encoding="utf-8") as f:
            lessons = json.load(f)
        print(f"عدد الدروس المحفوظة: {len(lessons)}")
        for i, lesson in enumerate(lessons, 1):
            print(f"\n  الدرس {i}:")
            print(f"    السؤال: {lesson['question'][:50]}...")
            print(f"    الاستراتيجية: {lesson['strategy']}")
            print(f"    النتيجة: {lesson['outcome']}")
            if lesson.get('reason'):
                print(f"    السبب: {lesson['reason'][:80]}...")
    else:
        print("❌ لم يتم إنشاء ملف الذاكرة.")

    # ==========================================================
    # ملخص
    # ==========================================================
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    # هل تم استخدام الذاكرة في أي محاولة؟
    test2_used_memory = ctx2.metadata.get("plan", {}).get("episodic_warnings_used", False)
    test3_used_memory = ctx3.metadata.get("plan", {}).get("episodic_warnings_used", False)

    if test2_used_memory or test3_used_memory:
        print("✅ الذاكرة تعمل: تم استخدام الدروس في المحاولات اللاحقة.")
    else:
        print("⚠️  الذاكرة محفوظة، لكن لم يتم استخدامها في الـ Planner بعد.")
        print("   السبب: deterministic routing يتجاوز LLM.")
        print("   الحل: تشغيل RAG API أو استخدام أسئلة بدون keywords.")


if __name__ == "__main__":
    asyncio.run(main())