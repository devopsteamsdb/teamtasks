# -*- coding: utf-8 -*-
"""
Quick targeted test for previously failed queries to verify new parsing and fallback.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from ai_tools import detect_fallback_action, is_user_requesting_creation, is_user_requesting_mutation

TEST_CASES = [
    (13, "משימה 10 תקועה, שים אותה בעיכוב", "edit_task"),
    (14, "תחזיר את משימה 1 לטרם החל", "edit_task"),
    (18, "משימה 6 הסתיימה בהצלחה", "edit_task"),
    (21, "תוסיף משימה חדשה בשם 'בדיקת גיבויים שבועית' בפרויקט שדרוג תשתיות ענן ו-Kubernetes", "create_task"),
    (22, "פתח משימה חדשה לאלעד שנקראת 'הגדרת התראות PagerDuty' בעדיפות גבוהה", "create_task"),
    (23, "תוסיף משימה 'עדכון תעודות SSL' לדוד עם יעד למחר", "create_task"),
    (24, "צור משימה דחופה לנועה: 'בדיקת קריסות באייפון' עם הערות 'דחוף מאוד לפני ההשקה'", "create_task"),
    (25, "תוסיף משימה חדשה 'שדרוג Node.js' לצוות Backend עם 8 שעות משוערות", "create_task"),
    (26, "פתח פרויקט חדש בשם 'אבטחת שרשרת אספקה' לצוות אבטחת מידע", "create_project"),
    (28, "צור משימה עם צ'קליסט: 'התקנת שרת חדש' בפרויקט שדרוג תשתיות ענן ו-Kubernetes עם תתי משימות: 'הזמנת חומרה', 'התקנת לינוקס', 'חיבור לרשת'", "create_task"),
    (30, "שים משימה חדשה 'כתיבת תיעוד API' בתהליך בעדיפות בינונית", "create_task"),
    (32, "תוריד את אלכס ממשימה 4", "edit_task"),
    (33, "תשנה את העדיפות של משימה 6 לגבוהה", "edit_task"),
    (34, "תעדכן את משימה 2 שהעדיפות שלה נמוכה", "edit_task"),
    (35, "תוסיף הערה למשימה 3: 'ממתינים לאישור מנהל'", "edit_task"),
    (36, "תשנה את השם של משימה 11 ל-'מסך פרופיל מעודכן 2026'", "edit_task"),
    (37, "תעדכן את תאריך היעד של משימה 8 ל-15/11/2026", "edit_task"),
    (38, "שים את משימה 14 בעדיפות דחופה", "edit_task"),
    (39, "תקצה את משימה 10 למאיה בלבד", "edit_task"),
    (40, "תוסיף תת משימה 'בדיקת עומסים' למשימה 2", "edit_task"),
]

with app.app_context():
    all_ok = True
    for q_id, q_text, exp_act in TEST_CASES:
        is_mut = is_user_requesting_mutation(q_text)
        is_creat = is_user_requesting_creation(q_text)
        fb = detect_fallback_action(q_text, "")
        act_name = fb[0]['action'] if fb else None
        params = fb[0]['params'] if fb else {}
        ok = (act_name == exp_act)
        status = "[OK]  " if ok else "[FAIL]"
        if not ok:
            all_ok = False
        print(f"{status} #{q_id:02d}: {act_name} (exp {exp_act}) | mut={is_mut}, creat={is_creat} | params={params}")

    print("=" * 60)
    print("ALL TARGETED CASES PASSED:" if all_ok else "SOME CASES FAILED:", all_ok)
