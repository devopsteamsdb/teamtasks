# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
client = app.test_client()

queries = [
    (21, "תוסיף משימה חדשה בשם 'בדיקת גיבויים שבועית' בפרויקט שדרוג תשתיות ענן ו-Kubernetes"),
    (22, "פתח משימה חדשה לאלעד שנקראת 'הגדרת התראות PagerDuty' בעדיפות גבוהה"),
    (23, "תוסיף משימה 'עדכון תעודות SSL' לדוד עם יעד למחר"),
    (24, "צור משימה דחופה לנועה: 'בדיקת קריסות באייפון' עם הערות 'דחוף מאוד לפני ההשקה'"),
    (25, "תוסיף משימה חדשה 'שדרוג Node.js' לצוות Backend עם 8 שעות משוערות"),
    (28, "צור משימה עם צ'קליסט: 'התקנת שרת חדש' בפרויקט שדרוג תשתיות ענן ו-Kubernetes עם תתי משימות: 'הזמנת חומרה', 'התקנת לינוקס', 'חיבור לרשת'"),
    (30, "שים משימה חדשה 'כתיבת תיעוד API' בתהליך בעדיפות בינונית")
]

with app.app_context():
    for q_id, q_text in queries:
        resp = client.post('/api/ai/chat', json={'message': q_text, 'history': []})
        data = resp.get_json() or {}
        acts = [a.get('action') for a in data.get('actions', [])]
        print(f"#{q_id:02d}: status={resp.status_code} acts={acts} desc={[a.get('description') for a in data.get('actions', [])]}")
