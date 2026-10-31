"""
Seed Data Script for TeamTasks
Generates realistic Israeli tech team mock data:
- Teams (DevOps, Frontend, Backend, QA, Security, System)
- Team members with 3D superhero avatars and dual team memberships
- Realistic projects with consistent team assignments
- Rich tasks across all statuses (Done, In Progress, Delayed, Not Started) and priorities
- Interactive checklist subtasks with accurate completion progress
- Discussion comments from team members with realistic avatars and relative timestamps
- Special days (company events, holidays, releases, code freeze)
- Realistic Gantt/Timeline scheduling around current date
"""

import sys
import random
from datetime import date, datetime, timedelta, timezone
from app import app, db, Team, TeamMember, Project, Task, SpecialDay, TaskComment, Subtask

def build_mock_dataset():
    """Returns the structured blueprint for realistic mock data."""
    teams_def = [
        {'name_en': 'devops', 'name_he': 'צוות DevOps'},
        {'name_en': 'frontend', 'name_he': 'צוות Frontend'},
        {'name_en': 'backend', 'name_he': 'צוות Backend'},
        {'name_en': 'qa', 'name_he': 'צוות QA ואוטומציה'},
        {'name_en': 'security', 'name_he': 'צוות אבטחת מידע'},
        {'name_en': 'system', 'name_he': 'צוות סיסטם ותשתיות'}
    ]

    members_def = [
        # DevOps
        ('david', 'דוד עמר', 'devops', 'avatar_1.png'),
        ('michal', 'מיכל לוי', 'devops', 'avatar_2.png'),
        ('yossi', 'יוסי מזרחי', 'devops', 'avatar_3.png'),
        ('elad', 'אלעד קורן', 'devops', 'avatar_4.png'),
        # Frontend
        ('dana', 'דנה רון', 'frontend', 'avatar_5.png'),
        ('roei', 'רועי שמיר', 'frontend', 'avatar_6.png'),
        ('noa', 'נועה ברק', 'frontend', 'avatar_7.png'),
        ('maya', 'מאיה גל', 'frontend', 'avatar_8.png'),
        # Backend
        ('itay', 'איתי גולן', 'backend', 'avatar_9.png'),
        ('tamar', 'תמר שהם', 'backend', 'avatar_10.png'),
        ('guy', 'גיא ורדי', 'backend', 'avatar_11.png'),
        ('alon', 'אלון שחר', 'backend', 'avatar_12.png'),
        # QA
        ('omer', 'עומר דהן', 'qa', 'avatar_13.png'),
        ('ron', 'רון אשכנזי', 'qa', 'avatar_14.png'),
        ('gal', 'גל סופר', 'qa', 'avatar_15.png'),
        ('shir', 'שיר כץ', 'qa', 'avatar_16.png'),
        # Security
        ('shay', 'שי ארז', 'security', 'avatar_17.png'),
        ('slava', 'סלבה פלדמן', 'security', 'avatar_18.png'),
        # System
        ('eli', 'אלי כהן', 'system', 'avatar_19.png'),
        ('alex', 'אלכס פרידמן', 'system', 'avatar_20.png'),
    ]

    projects_def = [
        {
            'name': 'שדרוג תשתיות ענן ו-Kubernetes',
            'team_keys': ['devops', 'system'],
            'primary_team': 'devops',
            'tasks': [
                {
                    'task': 'הקמת קלאסטר EKS וסביבות פיתוח',
                    'notes': 'הקמת קלאסטר מנוהל EKS ב-AWS עבור שירותי הפיתוח והבדיקות, כולל תצורת רשת מאובטחת.',
                    'members': ['david', 'elad'],
                    'status': 'status-done',
                    'priority': 'high',
                    'start_offset': -18,
                    'duration': 8,
                    'hours': 36.0,
                    'subtasks': [
                        'הגדרת VPC, תתי רשתות ו-NAT Gateways',
                        'יצירת קלאסטר EKS עם Managed Node Groups',
                        'התקנת Cert-Manager ו-ExternalDNS',
                        'הגדרת חיבורי SSO ו-RBAC למפתחים'
                    ],
                    'comments': [
                        ('david', 'הקלאסטר הוקם בהצלחה ומוכן לקבלת עומסים.', 11),
                        ('elad', 'בדקתי את חיבורי ה-SSO מול ספק הזהויות, הכל עובד חלק ומאומת.', 10)
                    ]
                },
                {
                    'task': 'מיגרציה ל-Terraform Cloud וניהול State',
                    'notes': 'העברת כל ה-Terraform states מ-S3 מקומי ל-Terraform Cloud עם סביבות עבודה מנוהלות.',
                    'members': ['michal', 'david'],
                    'status': 'status-inprogress',
                    'priority': 'high',
                    'start_offset': -5,
                    'duration': 12,
                    'hours': 28.0,
                    'subtasks': [
                        'מיפוי כל ה-State files הקיימים ב-S3',
                        'הגדרת Workspaces ב-Terraform Cloud',
                        'הגדרת הרשאות וחיבור ל-GitHub Actions',
                        'נעילת גישה ל-State הישן ובדיקת הרצה סופית'
                    ],
                    'comments': [
                        ('michal', 'העברנו כבר 12 Workspaces, נשארו עוד 3 מורכבים של הרשת הראשית.', 2)
                    ]
                },
                {
                    'task': 'הגדרת Helm Charts ו-ArgoCD ל-GitOps',
                    'notes': 'מימוש תהליכי פריסה אוטומטיים מבוססי GitOps בעזרת ArgoCD ותבניות Helm אחידות.',
                    'members': ['yossi'],
                    'status': 'status-inprogress',
                    'priority': 'medium',
                    'start_offset': -2,
                    'duration': 10,
                    'hours': 20.0,
                    'subtasks': [
                        'התקנת ArgoCD בקלאסטר המרכזי',
                        'כתיבת Helm Chart אחיד למיקרו-שירותים',
                        'חיבור Webhooks לקבלת התראות סטטוס ב-Slack'
                    ],
                    'comments': [
                        ('yossi', 'יצרנו תבנית מצוינת ל-Helm Chart, צוותי הפיתוח מתחילים להשתמש בה.', 1)
                    ]
                },
                {
                    'task': 'שדרוג Ingress Controller לגרסה 1.9',
                    'notes': 'שדרוג בקר ה-Ingress של NGINX לגרסה עדכנית לתיקון חולשות אבטחה.',
                    'members': ['david', 'alex'],
                    'status': 'status-delayed',
                    'priority': 'low',
                    'start_offset': -7,
                    'duration': 9,
                    'hours': 14.0,
                    'subtasks': [
                        'בדיקת תאימות של הגרסה החדשה בסביבת Staging',
                        'תיאום חלון השבתה ועדכון פרודקשן',
                        'מעקב שגיאות ב-Grafana לאחר השדרוג'
                    ],
                    'comments': [
                        ('alex', 'נמצאה בעיית תאימות עם אחד ה-Annotations הישנים, ממתינים לתיקון לפני פרודקשן.', 3),
                        ('david', 'הפעלנו גרסת Canary לבדיקה נקודתית בינתיים.', 1)
                    ]
                },
                {
                    'task': 'הטמעת ניטור מתקדם עם Prometheus & Grafana',
                    'notes': 'איסוף מטריקות תשתית ומערכת, דשבורדים ויזואליים והתרעות סף.',
                    'members': ['elad'],
                    'status': 'status-notstarted',
                    'priority': 'medium',
                    'start_offset': 4,
                    'duration': 14,
                    'hours': 24.0,
                    'subtasks': [
                        'התקנת Kube-Prometheus-Stack',
                        'בניית דשבורדים למדידת תעבורה ומשאבים',
                        'הגדרת חוקי התראות (Alertmanager)'
                    ],
                    'comments': []
                },
                {
                    'task': 'אופטימיזציית עלויות ענן (FinOps)',
                    'notes': 'סריקת משאבים עודפים, מחיקת דיסקים יתומים ורכישת התחייבויות שמורות.',
                    'members': ['michal'],
                    'status': 'status-notstarted',
                    'priority': 'none',
                    'start_offset': None,
                    'duration': None,
                    'hours': 16.0,
                    'subtasks': [
                        'סריקת דיסקים ו-Snapshots לא פעילים',
                        'רכישת Savings Plans ו-Reserved Instances'
                    ],
                    'comments': []
                }
            ]
        },
        {
            'name': 'אפליקציית מובייל ללקוחות',
            'team_keys': ['frontend', 'backend'],
            'primary_team': 'frontend',
            'tasks': [
                {
                    'task': 'עיצוב ומימוש מסך כניסה ואימות ביומטרי',
                    'notes': 'כניסה מהירה בעזרת FaceID / Fingerprint ושמירה מאובטחת של אסימוני זיהוי.',
                    'members': ['dana', 'roei'],
                    'status': 'status-done',
                    'priority': 'high',
                    'start_offset': -21,
                    'duration': 9,
                    'hours': 32.0,
                    'subtasks': [
                        'תמיכה ב-FaceID וטביעת אצבע במכשירי iOS ו-Android',
                        'אימות דו-שלבי באמצעות SMS / OTP',
                        'שמירת Tokens מאובטחת ב-KeyStore וב-Keychain'
                    ],
                    'comments': [
                        ('dana', 'האימות הביומטרי עבר את מבדק ה-QA בהצלחה מלאה.', 12),
                        ('roei', 'מנגנון ה-Refresh Token עובד בצורה חלקה.', 11)
                    ]
                },
                {
                    'task': 'אינטגרציה לתשלומים מהירים (Apple Pay & Google Pay)',
                    'notes': 'הטמעת SDK לסליקה בלחיצה אחת עם תמיכה בארנקים דיגיטליים.',
                    'members': ['roei', 'itay'],
                    'status': 'status-inprogress',
                    'priority': 'high',
                    'start_offset': -4,
                    'duration': 11,
                    'hours': 40.0,
                    'subtasks': [
                        'חיבור מול ספק הסליקה ואימות Webhooks',
                        'מימוש תהליך תשלום ב-iOS עם Apple Pay',
                        'מימוש תהליך תשלום ב-Android עם Google Pay',
                        'טיפול בשגיאות תקשורת ושחזור עסקאות שנכשלו'
                    ],
                    'comments': [
                        ('roei', 'סיימנו את צד ה-iOS ונבדק בסביבת Sandbox, עכשיו עוברים ל-Android SDK.', 2),
                        ('itay', 'ה-Endpoint לסליקה ב-Backend מוכן ומחכה לבדיקות.', 1)
                    ]
                },
                {
                    'task': 'התראות Push בזמן אמת עם Firebase',
                    'notes': 'שליחת עדכוני סטטוס הזמנה, מבצעים והודעות שירות למשתמשי האפליקציה.',
                    'members': ['noa'],
                    'status': 'status-inprogress',
                    'priority': 'medium',
                    'start_offset': -1,
                    'duration': 8,
                    'hours': 18.0,
                    'subtasks': [
                        'הגדרת פרויקט ב-Firebase Console והורדת קבצי קונפיגורציה',
                        'אינטגרציה של ה-SDK באפליקציה ורישום Token',
                        'בניית שירות ב-Backend לשליחת התראות מפולחות'
                    ],
                    'comments': [
                        ('noa', 'נבדקה קבלת Push בשני המכשירים - ההתראה מגיעה תוך שניות בודדות.', 1)
                    ]
                },
                {
                    'task': 'אופטימיזציית ביצועים וטעינת תמונות',
                    'notes': 'שיפור זמני רינדור וגלילה חלקה של קטלוג המוצרים במובייל.',
                    'members': ['maya', 'omer'],
                    'status': 'status-delayed',
                    'priority': 'medium',
                    'start_offset': -6,
                    'duration': 10,
                    'hours': 22.0,
                    'subtasks': [
                        'המרת תמונות לפורמט WebP ב-CDN',
                        'מימוש מנגנון Caching מקומי במכשיר',
                        'מדידת זמני רינדור בעזרת כלי ביצועים'
                    ],
                    'comments': [
                        ('maya', 'גילינו צריכת זיכרון חריגה בגלילה מהירה ברשימות ארוכות, בוחנים פתרון וירטואליזציה.', 3),
                        ('omer', 'הכנתי תסריט בדיקה לבדיקת צריכת RAM במכשירי קצה ישנים.', 2)
                    ]
                },
                {
                    'task': 'מסך פרופיל אישי והגדרות אבטחה',
                    'notes': 'ניהול פרטי משתמש, שינוי סיסמה והתנתקות מכל המכשירים המחוברים.',
                    'members': ['dana'],
                    'status': 'status-notstarted',
                    'priority': 'low',
                    'start_offset': 6,
                    'duration': 9,
                    'hours': 15.0,
                    'subtasks': [
                        'עריכת פרטים אישיים ותמונת פרופיל',
                        'ניהול התקנים מחוברים וניתוק מרחוק'
                    ],
                    'comments': []
                }
            ]
        },
        {
            'name': 'פורטל שירות עצמי לעובדים',
            'team_keys': ['frontend', 'backend', 'devops'],
            'primary_team': 'backend',
            'tasks': [
                {
                    'task': 'הטמעת מערכת SSO מבוססת SAML ו-OIDC',
                    'notes': 'אימות אחוד לכל מערכות החברה עם סנכרון משתמשים וקבוצות מ-Azure AD.',
                    'members': ['itay', 'david'],
                    'status': 'status-done',
                    'priority': 'high',
                    'start_offset': -25,
                    'duration': 12,
                    'hours': 45.0,
                    'subtasks': [
                        'חיבור מול שרתי Azure AD וקריאת Claims',
                        'ניהול הרשאות וקבוצות משתמשים בבסיס הנתונים',
                        'בדיקות חדירות לאימות וסשנים מאובטחים'
                    ],
                    'comments': [
                        ('itay', 'כל עובדי החברה הועברו לחיבור SSO ללא תקלות מדווחות.', 15)
                    ]
                },
                {
                    'task': 'טופס הגשת בקשות רכש וציוד מחשוב',
                    'notes': 'טופס דינמי להזמנת ציוד, מחשבים וציוד היקפי עם אישור מנהל אוטומטי.',
                    'members': ['dana', 'tamar'],
                    'status': 'status-inprogress',
                    'priority': 'medium',
                    'start_offset': -3,
                    'duration': 9,
                    'hours': 24.0,
                    'subtasks': [
                        'בניית ממשק משתמש אינטואיטיבי עם טפסים דינמיים',
                        'מנגנון אישורים אוטומטי מול מנהלים ישירים בדוא"ל',
                        'התממשקות למערכת מלאי ומשלוחים'
                    ],
                    'comments': [
                        ('dana', 'הממשק הוצג לצוות משאבי אנוש ואושר במלואו.', 2)
                    ]
                },
                {
                    'task': 'מערכת דיווח נוכחות וחופשות',
                    'notes': 'לוח שנה אינטראקטיבי להגשת בקשות חופשה וחישוב יתרות צבורות.',
                    'members': ['tamar', 'alon'],
                    'status': 'status-inprogress',
                    'priority': 'high',
                    'start_offset': 0,
                    'duration': 12,
                    'hours': 30.0,
                    'subtasks': [
                        'לוח שנה ויזואלי להצגת ימי חופשה וחגים',
                        'חישוב יתרת ימי חופשה ומחלה צבורים',
                        'ייצוא נתונים חודשי למערכת שכר'
                    ],
                    'comments': [
                        ('tamar', 'סיימנו את הלוגיקה של חישוב הצבירה החודשית לפי ותק.', 0)
                    ]
                },
                {
                    'task': 'מרכז ידע ודוקומנטציה פנים-ארגוני',
                    'notes': 'מאגר נהלים ומדריכים עם חיפוש מהיר ועורך Markdown עשיר.',
                    'members': ['noa'],
                    'status': 'status-notstarted',
                    'priority': 'low',
                    'start_offset': 8,
                    'duration': 14,
                    'hours': 20.0,
                    'subtasks': [
                        'מנוע חיפוש מהיר במסמכים ומדריכים',
                        'עורך Markdown עשיר לעדכון נהלים'
                    ],
                    'comments': []
                }
            ]
        },
        {
            'name': 'מיגרציה למסד נתונים וביצועים',
            'team_keys': ['backend', 'system'],
            'primary_team': 'backend',
            'tasks': [
                {
                    'task': 'הגדרת רפליקציה לקריאה עם Read Replicas',
                    'notes': 'הקמת עותקי קריאה מרובים להורדת עומס מהמסד הראשי ושיפור זמני תגובה.',
                    'members': ['alon', 'alex'],
                    'status': 'status-done',
                    'priority': 'high',
                    'start_offset': -22,
                    'duration': 10,
                    'hours': 35.0,
                    'subtasks': [
                        'הקמת 2 Read Replicas ב-Multi-AZ',
                        'הפניית שאילתות כבדות ודוחות לקריאה בלבד',
                        'בדיקת זמני Replication Lag תחת עומס'
                    ],
                    'comments': [
                        ('alon', 'ה-Replication Lag נשמר מתחת ל-8ms, שיפור משמעותי בזמני תגובה!', 13)
                    ]
                },
                {
                    'task': 'העברת סכמות ואינדקסים ל-PostgreSQL 16',
                    'notes': 'שדרוג גרסת מנוע מסד הנתונים ומיצוי שיפורי ביצועים באינדקסים.',
                    'members': ['guy', 'alon'],
                    'status': 'status-inprogress',
                    'priority': 'high',
                    'start_offset': -6,
                    'duration': 14,
                    'hours': 38.0,
                    'subtasks': [
                        'המרת סכמת הנתונים והתאמת Foreign Keys',
                        'אופטימיזציית אינדקסים מורכבים ו-Partial Indexes',
                        'הרצת בדיקות נסיגה ואימות שלמות הנתונים'
                    ],
                    'comments': [
                        ('guy', 'זיהינו כמה שאילתות קריטיות שהאינדקס החדש האיץ פי 4.', 2)
                    ]
                },
                {
                    'task': 'מבדקי ביצועים ועומסים בטרנזקציות שיא',
                    'notes': 'סימולציית עומסי שיא של ימי מבצעים עם k6 לאיתור צווארי בקבוק ונעילות.',
                    'members': ['itay', 'omer'],
                    'status': 'status-delayed',
                    'priority': 'medium',
                    'start_offset': -5,
                    'duration': 10,
                    'hours': 24.0,
                    'subtasks': [
                        'בניית תסריט עומס של 5,000 בקשות בשנייה ב-k6',
                        'זיהוי צווארי בקבוק בנעילות שורות (Row Locks)',
                        'הגדרת Connection Pooling עם PgBouncer'
                    ],
                    'comments': [
                        ('itay', 'נתקלנו במיצוי חיבורים בעומס מעל 3,000 RPS, מתקינים PgBouncer כעת.', 3),
                        ('omer', 'התסריטים מוכנים ומוכנים להרצה חוזרת ברגע שה-Pooler יוגדר.', 1)
                    ]
                },
                {
                    'task': 'מנגנון ארכוב נתונים ישנים (Data Retention)',
                    'notes': 'מחיקה אוטומטית של רשומות היסטוריות וייצוא נתונים ישנים לאחסון קר.',
                    'members': ['alon'],
                    'status': 'status-notstarted',
                    'priority': 'low',
                    'start_offset': None,
                    'duration': None,
                    'hours': 16.0,
                    'subtasks': [
                        'הגדרת מדיניות מחיקת לוגים ונתונים מעל שנתיים',
                        'יצירת תהליך Cron לילי לייצוא ל-Cold Storage ב-S3'
                    ],
                    'comments': []
                }
            ]
        },
        {
            'name': 'אוטומציית בדיקות ו-CI/CD',
            'team_keys': ['qa', 'devops'],
            'primary_team': 'qa',
            'tasks': [
                {
                    'task': 'בניית תשתית בדיקות E2E עם Playwright',
                    'notes': 'פיתוח בדיקות קצה-לקצה אוטומטיות בתהליך ה-CI לתרחישי הליבה של האפליקציה.',
                    'members': ['omer', 'ron'],
                    'status': 'status-done',
                    'priority': 'high',
                    'start_offset': -20,
                    'duration': 11,
                    'hours': 40.0,
                    'subtasks': [
                        'הגדרת פרויקט Playwright עם TypeScript',
                        'כתיבת 25 בדיקות תרחישי ליבה של משתמשים',
                        'הפקת דוחות HTML וצילומי וידאו של כשלונות'
                    ],
                    'comments': [
                        ('omer', 'כל 25 הבדיקות עוברות בהצלחה מלאה, זמן ריצה כולל 42 שניות במקביל.', 9)
                    ]
                },
                {
                    'task': 'שילוב סריקות אבטחה SAST ו-DAST ב-Pipeline',
                    'notes': 'סריקת קוד אוטומטית לאיתור חולשות אבטחה ופגיעויות ספריות קוד פתוח בכל Pull Request.',
                    'members': ['gal', 'shay'],
                    'status': 'status-inprogress',
                    'priority': 'high',
                    'start_offset': -3,
                    'duration': 10,
                    'hours': 26.0,
                    'subtasks': [
                        'הגדרת סריקת קוד סטטית עם SonarQube',
                        'סריקת חולשות ספריות עם Dependabot ו-Snyk',
                        'חסימת מיזוג PR במקרה של חולשה בדרגת High או Critical'
                    ],
                    'comments': [
                        ('gal', 'SonarQube כבר רץ על כל PR ומדווח סטטוס ישירות ב-GitHub.', 2)
                    ]
                },
                {
                    'task': 'הקמת סביבת Staging דינמית לכל Pull Request',
                    'notes': 'פריסת סביבת Preview זמנית לבדיקה ידנית ואוטומטית לפני מיזוג ל-main.',
                    'members': ['shir', 'yossi'],
                    'status': 'status-delayed',
                    'priority': 'medium',
                    'start_offset': -5,
                    'duration': 9,
                    'hours': 18.0,
                    'subtasks': [
                        'יצירת Ephemeral Environments ב-Kubernetes לפי ענף',
                        'חיבור DNS דינמי לסביבה זמנית (preview-branch)',
                        'ניקוי אוטומטי של משאבים בסגירת ה-PR'
                    ],
                    'comments': [
                        ('shir', 'נתקלנו במגבלת מכסות שמות מתחם ב-Route53, בודקים אלטרנטיבה.', 2),
                        ('yossi', 'ביקשנו העלאת מכסה מ-AWS Support, צפוי להיפתר בקרוב.', 1)
                    ]
                },
                {
                    'task': 'מערכת דיווח תוצאות בדיקות ל-Slack',
                    'notes': 'שליחת סיכומי ריצת בדיקות והתראות מיידיות על תקלות לערוץ הפיתוח ב-Slack.',
                    'members': ['ron'],
                    'status': 'status-notstarted',
                    'priority': 'low',
                    'start_offset': 5,
                    'duration': 7,
                    'hours': 12.0,
                    'subtasks': [
                        'בניית Bot לשליחת סיכום ריצת בדיקות יומית',
                        'התראה מיידית על שבירת Build בענף Main'
                    ],
                    'comments': []
                }
            ]
        },
        {
            'name': 'תאימות אבטחת מידע ו-SOC2',
            'team_keys': ['security', 'devops'],
            'primary_team': 'security',
            'tasks': [
                {
                    'task': 'הטמעת אימות דו-שלבי (MFA) חובה לכל הגישות',
                    'notes': 'אכיפת MFA דרך Authenticator App לכל המערכות הארגוניות וביטול סיסמאות סטטיות.',
                    'members': ['shay', 'slava'],
                    'status': 'status-done',
                    'priority': 'high',
                    'start_offset': -28,
                    'duration': 10,
                    'hours': 30.0,
                    'subtasks': [
                        'אכיפת MFA דרך Authenticator App לכל המשתמשים',
                        'ביטול סיסמאות סטטיות בגישות SSH ו-VPN',
                        'הדרכת עובדים והסבר על מדיניות אבטחה'
                    ],
                    'comments': [
                        ('shay', '100% מהעובדים פעילים עם MFA ללא חריגות.', 18)
                    ]
                },
                {
                    'task': 'הגדרת מדיניות DLP וסינון דליפת מידע',
                    'notes': 'זיהוי וחסימת העלאת קבצים רגישים וכרטיסי אשראי בערוצי תקשורת פנימיים.',
                    'members': ['slava'],
                    'status': 'status-inprogress',
                    'priority': 'high',
                    'start_offset': -7,
                    'duration': 14,
                    'hours': 32.0,
                    'subtasks': [
                        'זיהוי וחסימת העלאת קבצים רגישים (כרטיסי אשראי, ת.ז)',
                        'הגדרת התראות לצוות SOC על פעילות חשודה',
                        'דוח חודשי של ניסיונות שיתוף חריגים'
                    ],
                    'comments': [
                        ('slava', 'החוקים נבדקים כרגע במצב Audit בלבד לפני מעבר ל-Block מלא.', 3)
                    ]
                },
                {
                    'task': 'מבדק חדירות אפליקטיבי ותשתיות חיצוני',
                    'notes': 'מבדק פנטיסינג מקיף של חברה חיצונית לקראת חידוש הסמכת SOC2 ו-ISO 27001.',
                    'members': ['shay', 'david'],
                    'status': 'status-inprogress',
                    'priority': 'medium',
                    'start_offset': -2,
                    'duration': 12,
                    'hours': 35.0,
                    'subtasks': [
                        'בחירת ספק מבדקי חדירות מוסמך',
                        'הכנת סביבת בדיקות ייעודית עם נתוני Mock',
                        'מעקב ותיקון ממצאים לפי דו"ח הפנטיסינג'
                    ],
                    'comments': [
                        ('shay', 'הספק החל בבדיקות אתמול, ממתינים לדו"ח ראשוני בתחילת השבוע הבא.', 1)
                    ]
                },
                {
                    'task': 'סקירת הרשאות גישה תקופתית (User Access Review)',
                    'notes': 'ביקורת הרשאות רבעונית בכל מערכות ה-Cloud וביטול גישות של עובדים שעזבו.',
                    'members': ['slava'],
                    'status': 'status-notstarted',
                    'priority': 'low',
                    'start_offset': 10,
                    'duration': 8,
                    'hours': 14.0,
                    'subtasks': [
                        'ייצוא רשימת כל המשתמשים וההרשאות מ-AWS ו-GitHub',
                        'שליחת טופס אישור למנהלים להסרת הרשאות עודפות'
                    ],
                    'comments': []
                }
            ]
        },
        {
            'name': 'שדרוג רשתות ארגוניות ו-WiFi 6',
            'team_keys': ['system', 'security'],
            'primary_team': 'system',
            'tasks': [
                {
                    'task': 'החלפת מתגי Access וקונפיגורציית VLANs',
                    'notes': 'התקנת מתגים מנוהלים חדשים בארונות תקשורת והפרדה מוחלטת בין רשתות.',
                    'members': ['eli', 'alex'],
                    'status': 'status-done',
                    'priority': 'medium',
                    'start_offset': -24,
                    'duration': 8,
                    'hours': 28.0,
                    'subtasks': [
                        'התקנת מתגים חדשים בארונות התקשורת',
                        'הפרדת רשתות VLAN: אורחים, עובדים, שרתים ומצלמות',
                        'בדיקת שרידות וחיבורי Trunk כפולים'
                    ],
                    'comments': [
                        ('eli', 'ההחלפה בוצעה בסוף השבוע בהצלחה מלאה וללא השבתה.', 16)
                    ]
                },
                {
                    'task': 'פריסת נקודות גישה WiFi 6 בכל קומות המשרד',
                    'notes': 'שיפור מהירות הקליטה והכיסוי האלחוטי בעזרת Access Points חדישות.',
                    'members': ['alex'],
                    'status': 'status-inprogress',
                    'priority': 'medium',
                    'start_offset': -4,
                    'duration': 9,
                    'hours': 20.0,
                    'subtasks': [
                        'סקר אתר (Site Survey) למיפוי עוצמות קליטה',
                        'התקנת 18 יחידות AP חדשות בתקרה',
                        'כוונון תדרים וערוצים למניעת הפרעות הדדיות'
                    ],
                    'comments': [
                        ('alex', 'קומות 3 ו-4 סיימו, נותרה קומה 2 בלבד.', 2)
                    ]
                },
                {
                    'task': 'שדרוג רוחב פס סיב אופטי ראשי ל-10Gbps',
                    'notes': 'חיבור קו סיב כפול מחברות התקשורת להבטחת יתירות מלאה ורוחב פס מוגדל.',
                    'members': ['eli'],
                    'status': 'status-delayed',
                    'priority': 'high',
                    'start_offset': -8,
                    'duration': 14,
                    'hours': 30.0,
                    'subtasks': [
                        'הזמנת קו סיב כפול מחברות התקשורת',
                        'תיאום טכנאי להתקנת ציוד הקצה (CPE)',
                        'בדיקת מהירות ו-Failover אוטומטי בעומס'
                    ],
                    'comments': [
                        ('eli', 'ספק התקשורת דחה את הגעת הטכנאי עקב עבודות תשתית ברחוב.', 4)
                    ]
                }
            ]
        }
    ]

    today = date.today()
    special_days_def = [
        (today - timedelta(days=12), 'השקת גרסת Beta 2.0', 'other', '#9C27B0'),
        (today + timedelta(days=2), 'יום גיבוש מחלקתי', 'company_event', '#4CAF50'),
        (today + timedelta(days=8), 'חופשת סוף שבוע ארוך', 'holiday', '#E91E63'),
        (today + timedelta(days=15), 'הקפאת קוד לקראת גרסה (Code Freeze)', 'other', '#FF9800'),
        (today + timedelta(days=22), 'שחרור גרסה 3.0 לפרודקשן', 'other', '#2196F3'),
    ]

    return teams_def, members_def, projects_def, special_days_def


def seed(reset=True):
    """Seed database with complete, rich mock data."""
    with app.app_context():
        if reset:
            print("Dropping all existing tables...")
            db.drop_all()
            print("Creating all tables from scratch...")
            db.create_all()

        teams_def, members_def, projects_def, special_days_def = build_mock_dataset()

        # 1. Create Teams
        teams_map = {}
        for t_info in teams_def:
            team = Team(name_en=t_info['name_en'], name_he=t_info['name_he'])
            db.session.add(team)
            teams_map[t_info['name_en']] = team

        db.session.commit()
        print(f"Created {len(teams_map)} teams.")

        # 2. Create Members
        members_map = {}
        for en, he, team_key, avatar in members_def:
            primary_team = teams_map[team_key]
            member = TeamMember(
                name_en=en,
                name_he=he,
                team_id=primary_team.id,
                avatar_path=avatar
            )
            member.teams.append(primary_team)
            db.session.add(member)
            members_map[en] = member

        db.session.commit()
        print(f"Created {len(members_map)} members.")

        # 3. Create Projects, Tasks, Subtasks, Comments
        today = date.today()
        now_utc = datetime.now(timezone.utc)
        total_tasks = 0
        total_subtasks = 0
        total_comments = 0

        for p_def in projects_def:
            p_teams = [teams_map[k] for k in p_def['team_keys'] if k in teams_map]
            project = Project(
                name=p_def['name'],
                teams=p_teams,
                is_archived=False
            )
            db.session.add(project)
            db.session.flush()

            primary_team = teams_map.get(p_def['primary_team'], p_teams[0])

            for t_def in p_def['tasks']:
                # Dates
                s_date = None
                e_date = None
                if t_def['start_offset'] is not None and t_def['duration'] is not None:
                    s_date = today + timedelta(days=t_def['start_offset'])
                    e_date = s_date + timedelta(days=t_def['duration'])

                task = Task(
                    project_id=project.id,
                    project=project.name,
                    task=t_def['task'],
                    members=','.join(t_def['members']),
                    status=t_def['status'],
                    priority=t_def['priority'],
                    notes=t_def['notes'],
                    team_id=primary_team.id,
                    start_date=s_date,
                    end_date=e_date,
                    estimated_hours=t_def['hours'],
                    is_archived=False
                )
                db.session.add(task)
                db.session.flush()
                total_tasks += 1

                # Subtasks with appropriate completion state
                subtask_titles = t_def.get('subtasks', [])
                num_subtasks = len(subtask_titles)
                for idx, st_title in enumerate(subtask_titles):
                    # Determine completion status based on task status
                    if task.status == 'status-done':
                        is_comp = True
                    elif task.status == 'status-notstarted':
                        is_comp = False
                    elif task.status == 'status-inprogress':
                        # complete first 50-75%
                        is_comp = idx < max(1, int(num_subtasks * 0.6))
                    elif task.status == 'status-delayed':
                        # partial completion halted early
                        is_comp = idx == 0
                    else:
                        is_comp = False

                    subtask = Subtask(
                        task_id=task.id,
                        title=st_title,
                        is_completed=is_comp,
                        order=idx,
                        created_at=now_utc - timedelta(days=abs(t_def['start_offset'] or 5) + 2)
                    )
                    db.session.add(subtask)
                    total_subtasks += 1

                # Comments
                comments_list = t_def.get('comments', [])
                for author_en, content, days_ago in comments_list:
                    author_member = members_map.get(author_en)
                    if author_member:
                        author_name = author_member.name_he
                        author_avatar = author_member.avatar_path
                        member_id = author_member.id
                    else:
                        author_name = author_en
                        author_avatar = 'default.png'
                        member_id = None

                    comment = TaskComment(
                        task_id=task.id,
                        author_name=author_name,
                        author_avatar=author_avatar,
                        member_id=member_id,
                        content=content,
                        created_at=now_utc - timedelta(days=days_ago, hours=random.randint(1, 10))
                    )
                    db.session.add(comment)
                    total_comments += 1

        db.session.commit()
        print(f"Created {total_tasks} tasks with {total_subtasks} subtasks and {total_comments} comments across {len(projects_def)} projects.")

        # 4. Special Days
        for d, name, dtype, color in special_days_def:
            sd = SpecialDay(date=d, name=name, type=dtype, color=color)
            db.session.add(sd)

        db.session.commit()
        print(f"Created {len(special_days_def)} special days.")
        print("Mock data generation finished successfully!")


def enrich_existing():
    """Enriches existing tasks in the database with mock subtasks, comments, dates, and hours."""
    with app.app_context():
        tasks = Task.query.all()
        members = TeamMember.query.all()
        if not members:
            print("No members found. Running full seed instead...")
            seed(reset=False)
            return

        today = date.today()
        now_utc = datetime.now(timezone.utc)
        subtasks_added = 0
        comments_added = 0
        dates_updated = 0

        subtask_templates = [
            "הגדרת סביבת עבודה ותלויות",
            "כתיבת קוד ומימוש פונקציונלי",
            "בדיקות יחידה ואינטגרציה",
            "בדיקת קבלה של צוות QA",
            "תיעוד ועדכון Release Notes"
        ]

        comment_templates = [
            "התחלתי לעבוד על המשימה, נראה בכיוון הנכון.",
            "העברתי לסביבת בדיקות, אשמח לבדיקה ומשוב.",
            "הבדיקות עברו בהצלחה, ממתין לחלון פריסה.",
            "שים לב שיש תלות במשימה המקבילה.",
            "הכל עודכן ותקין בסביבת הייצור."
        ]

        for t in tasks:
            # Set dates if missing
            if not t.start_date:
                offset = random.randint(-10, 15)
                dur = random.randint(3, 10)
                t.start_date = today + timedelta(days=offset)
                t.end_date = t.start_date + timedelta(days=dur)
                dates_updated += 1
            if not t.estimated_hours:
                t.estimated_hours = float(random.randint(4, 30))

            # Add subtasks if none exist
            if not t.subtasks:
                count = random.randint(2, 4)
                for idx in range(count):
                    st_title = subtask_templates[idx % len(subtask_templates)]
                    is_comp = (t.status == 'status-done') or (t.status == 'status-inprogress' and idx == 0)
                    st = Subtask(
                        task_id=t.id,
                        title=f"{st_title} ({t.task[:15]})",
                        is_completed=is_comp,
                        order=idx,
                        created_at=now_utc - timedelta(days=random.randint(1, 10))
                    )
                    db.session.add(st)
                    subtasks_added += 1

            # Add comments if none exist
            if not t.comments and random.random() > 0.3:
                num_comments = random.randint(1, 2)
                for c_idx in range(num_comments):
                    m = random.choice(members)
                    comment = TaskComment(
                        task_id=t.id,
                        author_name=m.name_he,
                        author_avatar=m.avatar_path,
                        member_id=m.id,
                        content=random.choice(comment_templates),
                        created_at=now_utc - timedelta(days=random.randint(0, 5), hours=random.randint(1, 12))
                    )
                    db.session.add(comment)
                    comments_added += 1

        db.session.commit()
        print(f"Enriched existing database: {dates_updated} dates set, {subtasks_added} subtasks added, {comments_added} comments added.")


if __name__ == '__main__':
    if '--enrich' in sys.argv or '--append' in sys.argv:
        enrich_existing()
    else:
        seed(reset=True)
