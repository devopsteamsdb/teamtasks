import re
import json
import logging
from datetime import datetime, date, timedelta
from models import db, Team, TeamMember, Project, Task, SpecialDay

logger = logging.getLogger(__name__)

def parse_date_value(val):
    if not val or not str(val).strip():
        return None
    val_str = str(val).strip().lower()
    today = date.today()
    
    if val_str in ['today', 'היום']:
        return today
    if val_str in ['tomorrow', 'מחר']:
        return today + timedelta(days=1)
    if val_str in ['yesterday', 'אתמול']:
        return today - timedelta(days=1)
    if val_str in ['end of week', 'סוף השבוע']:
        # Next Friday
        days_ahead = 4 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return today + timedelta(days=days_ahead)
    if val_str in ['next week', 'שבוע הבא']:
        return today + timedelta(days=7)

    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y'):
        try:
            return datetime.strptime(val_str, fmt).date()
        except ValueError:
            continue
    return None

def resolve_member_names(members_input):
    """Converts a list or comma-string of member names (Hebrew or English) to standard lowercase name_en list."""
    if not members_input:
        return []
    if isinstance(members_input, str):
        members_input = [m.strip() for m in members_input.split(',') if m.strip()]

    all_members = TeamMember.query.all()
    he_to_en = {m.name_he.strip(): m.name_en.strip().lower() for m in all_members}
    en_names = {m.name_en.strip().lower() for m in all_members}

    resolved = []
    for item in members_input:
        cleaned = item.strip()
        cleaned_lower = cleaned.lower()
        if cleaned in he_to_en:
            resolved.append(he_to_en[cleaned])
        elif cleaned_lower in en_names:
            resolved.append(cleaned_lower)
        else:
            # Fuzzy match on Hebrew name
            found = False
            for he, en in he_to_en.items():
                if cleaned in he or he in cleaned:
                    resolved.append(en)
                    found = True
                    break
            if not found:
                resolved.append(cleaned_lower)
    return list(dict.fromkeys(resolved))

def resolve_project(project_val):
    """Finds or resolves project by ID or Name."""
    if not project_val:
        return None
    if isinstance(project_val, int) or (isinstance(project_val, str) and project_val.isdigit()):
        return db.session.get(Project, int(project_val))
    
    # By exact name
    proj = Project.query.filter_by(name=str(project_val).strip()).first()
    if proj:
        return proj
        
    # By case-insensitive/partial name
    all_projects = Project.query.all()
    val_clean = str(project_val).strip().lower()
    for p in all_projects:
        if p.name.strip().lower() == val_clean or val_clean in p.name.strip().lower():
            return p
    return None

def normalize_status(val):
    """Normalizes any status variant into standard teamtasks status."""
    if not val:
        return None
    val_str = str(val).strip().lower()
    
    if val_str in ['status-notstarted', 'status-inprogress', 'status-done', 'status-delayed']:
        return val_str

    # 1. Not started mappings (check FIRST so 'טרם החל' doesn't match 'החל')
    if any(k in val_str for k in ['notstarted', 'not_started', 'not-started', 'not started', 'טרם', 'לא החל', 'לא התחיל', 'פתוח', 'חדש', 'המתנה', 'pending']):
        return 'status-notstarted'
        
    # 2. Done mappings
    if any(k in val_str for k in ['done', 'completed', 'finished', 'הושלם', 'הושלמה', 'בוצע', 'בוצעה', 'הסתיים', 'הסתיימה', 'סיום', 'גמור', 'סיימתי']):
        return 'status-done'
        
    # 3. Delayed mappings
    if any(k in val_str for k in ['delayed', 'ממתין', 'מעוכב', 'מעוכבת', 'עיכוב', 'תקוע', 'stuck', 'blocked', 'hold']):
        return 'status-delayed'

    # 4. In-progress mappings
    if any(k in val_str for k in ['inprogress', 'in_progress', 'in-progress', 'in progress', 'בתהליך', 'תהליך', 'בביצוע', 'בעבודה', 'started', 'working', 'running']):
        return 'status-inprogress'

    if re.search(r'(?<!לא\s)(?<!טרם\s)\bהחל\b', val_str):
        return 'status-inprogress'

    return val_str

def resolve_task(params):
    """
    Intelligently resolves a Task instance from params which might have:
    - id, task_id, taskId (int, string, or string with #)
    - task, title, name, task_name, task_title, description
    - project / project_id (for narrowing down if ambiguous)
    Supports exact, case-insensitive, partial substring, and token overlap matching.
    """
    if not params:
        return None

    # Extract potential title text from various keys
    title_candidates = []
    for k in ['task', 'title', 'name', 'task_name', 'task_title', 'description']:
        val = params.get(k)
        if val and isinstance(val, str) and val.strip():
            title_candidates.append(val.strip())

    # 1. Try explicit ID
    raw_id = params.get('id') or params.get('task_id') or params.get('taskId')
    if raw_id is not None:
        digits = re.findall(r'\d+', str(raw_id))
        if digits:
            try:
                task_id = int(digits[0])
                t = db.session.get(Task, task_id)
                if t:
                    # If title candidates were also given, check against both project and task!
                    if title_candidates:
                        cand_text = " ".join(title_candidates).lower()
                        t_combined = f"{t.project or ''} {t.task or ''}".strip().lower()
                        cand_words = set(re.findall(r'[\w\-]+', cand_text))
                        stop_words = {
                            'של', 'את', 'עם', 'על', 'בסטטוס', 'סטטוס', 'משימה', 'משימת',
                            'לסטטוס', 'למצב', 'מצב', 'חדש', 'חדשה', 'הושלם', 'הושלמה',
                            'בתהליך', 'done', 'update', 'status', 'סמן', 'תסמן', 'לסמן',
                            'אותה', 'אותו', 'זה', 'את זה'
                        }
                        cand_words = {w for w in cand_words if len(w) > 1 and w not in stop_words}
                        t_words = set(re.findall(r'[\w\-]+', t_combined))
                        # If cand_words exist and match either task title or project name, it is a verified match!
                        if cand_words and not cand_words.intersection(t_words):
                            # Only switch if cand_words matches another task in the DB
                            for ot in Task.query.all():
                                if ot.id != t.id and any(w in ot.task.lower() for w in cand_words if len(w) >= 3):
                                    t = ot
                                    break
                    return t
            except (ValueError, TypeError):
                pass

    if not title_candidates:
        return None

    all_tasks = Task.query.all()
    if not all_tasks:
        return None

    for query in title_candidates:
        # Check if query itself is just a number like "56" or "#56"
        id_match = re.fullmatch(r'#?(\d+)', query)
        if id_match:
            t = db.session.get(Task, int(id_match.group(1)))
            if t:
                return t

        clean_query = query.strip().lower()
        clean_query = re.sub(r'^(?:תסמן|תסמני|סמן|סמני|תשנה|תשני|שנה|שני|תעדכן|תעדכני|עדכן|עדכני|תעביר|תעבירי|העבר|העבירי|תסגור|תסגרי|סגור|סגרי|תסיים|תסיימי|סיים|סיימי|תשלים|תשלימי|השלם|השלימי|בצע|בצעי|תבצע|תבצעי|הפוך|הפכי|תהפוך|תהפכי)\s+(?:את\s+)?(?:המשימה\s+|משימת\s+|משימה\s+)?', '', clean_query).strip()
        clean_query = re.sub(r'^(?:את\s+)?(?:משימת|משימה|task)\s+', '', clean_query).strip()
        # Strip trailing clauses
        clean_query = re.split(r'\s+(?:ש?הערות|ש?תאריך|לסטטוס|בסטטוס|לבתהליך|להושלם|הושלמה|הושלם|בוצע|בוצעה|כבוצע|כהושלם|כהושלמה|למעוכב|לארכיון)\b', clean_query)[0].strip()

        if not clean_query:
            continue

        # Exact match
        for t in all_tasks:
            if t.task.strip().lower() == clean_query:
                return t

        # Substring match (clean_query in t.task or t.task in clean_query)
        matches = []
        for t in all_tasks:
            t_name = t.task.strip().lower()
            if clean_query in t_name or t_name in clean_query:
                matches.append(t)

        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            # If project filter is present, narrow down
            proj_hint = str(params.get('project') or params.get('project_id') or '').strip().lower()
            if proj_hint:
                proj_matches = [t for t in matches if proj_hint in (t.project or '').lower()]
                if proj_matches:
                    return proj_matches[0]
            # Return shortest title match
            matches.sort(key=lambda t: len(t.task))
            return matches[0]

        # Token overlap matching (e.g. "vmware" + "שדרוג", "נתב" + "ראשי")
        query_words = set(re.findall(r'[\w\-]+', clean_query))
        stop_words = {'של', 'את', 'עם', 'על', 'בסטטוס', 'סטטוס', 'משימה', 'משימת', 'לסטטוס', 'למצב', 'מצב'}
        query_words = {w for w in query_words if len(w) > 1 and w not in stop_words}
        if query_words:
            scored = []
            for t in all_tasks:
                t_words = set(re.findall(r'[\w\-]+', t.task.strip().lower()))
                common = query_words.intersection(t_words)
                if common:
                    score = len(common) / len(query_words)
                    scored.append((score, t))
            if scored:
                scored.sort(key=lambda x: x[0], reverse=True)
                if scored[0][0] >= 0.5:
                    return scored[0][1]

    return None

def is_task_referenced_in_context(task, user_msg, history=None):
    """
    Checks if a given task was explicitly or contextually referenced in the user's message or recent conversation history.
    Prevents the LLM from arbitrarily picking/hallucinating a task from the system prompt when the user was vague.
    """
    if not task:
        return False
    
    user_text = str(user_msg or '').lower()
    context_text = user_text
    if history:
        for h in history[-4:]:
            context_text += " " + str(h.get('content', '')).lower()
            
    # 1. Direct ID match (e.g. "#56" or standalone "56")
    if re.search(rf'(?:^|[^\d])#?{task.id}(?:[^\d]|$)', context_text):
        return True
        
    # 2. Ordinal references if history contains task IDs
    if history:
        for ord_word, idx in [('ראשונה', 0), ('הראשונה', 0), ('שנייה', 1), ('השנייה', 1), ('שלישית', 2), ('השלישית', 2), ('אחרונה', -1), ('האחרונה', -1)]:
            if ord_word in user_text:
                for h in reversed(history):
                    if h.get('role') == 'assistant':
                        ids = re.findall(r'#(\d+)', h.get('content', ''))
                        if ids and abs(idx) < len(ids):
                            try:
                                if task.id == int(ids[idx]):
                                    return True
                            except (ValueError, IndexError):
                                pass

    # 3. Words overlap from task title
    t_clean = task.task.strip().lower()
    stop_words = {'של', 'את', 'עם', 'על', 'בסטטוס', 'סטטוס', 'משימה', 'משימת', 'לסטטוס', 'למצב', 'מצב', 'חדש', 'חדשה', 'פרויקט', 'צוות', 'the', 'a', 'an', 'to', 'in', 'for'}
    t_words = [w for w in re.findall(r'[\w\-]+', t_clean) if len(w) > 1 and w not in stop_words]
    
    if not t_words:
        return t_clean in context_text
        
    # Check if any significant word (length >= 3) from task title is in context_text
    for w in t_words:
        if len(w) >= 3 and w in context_text:
            return True
        
    # Check if whole title substring is in context
    if t_clean in context_text:
        return True
        
    return False

def is_project_referenced_in_context(project, user_msg, history=None):
    """Checks if a project was referenced in user message or history."""
    if not project:
        return False
    context_text = str(user_msg or '').lower()
    if history:
        for h in history[-4:]:
            context_text += " " + str(h.get('content', '')).lower()
    if re.search(rf'(?:^|[^\d])#?{project.id}(?:[^\d]|$)', context_text):
        return True
    p_clean = project.name.strip().lower()
    stop_words = {'פרויקט', 'של', 'את', 'עם', 'על', 'project'}
    p_words = [w for w in re.findall(r'[\w\-]+', p_clean) if len(w) > 1 and w not in stop_words]
    if not p_words:
        return p_clean in context_text
    return any(w in context_text for w in p_words if len(w) >= 3)

def is_user_requesting_mutation(user_msg):
    """
    Determines if the user's current message is actually requesting a modification/deletion/status-change
    of an existing task, project, team or member, rather than asking a question or requesting information.
    """
    if not user_msg:
        return False
    msg = str(user_msg).strip().lower()

    # 1. Pure informational prefixes/phrases that NEVER mutate unless explicit polite action wrapper
    is_inquiry_starter = bool(re.search(r'^(?:מה|מהם|מהן|מי\s+(?!תוכל|יכול)|איזה|איזו|אילו|כמה|למה|מדוע|איפה|היכן|מתי|האם|האם\s+יש|יש\s+משימות|רשימת|רשימה)\b', msg))
    is_view_starter = bool(re.search(r'^(?:תראה|הראה|להראות|הצג|תציג|להציג|פרט|תפרט|לפרט|ספר|תספר|בדוק|תבדוק|לבדוק|תסכם|סכם|לסכם)\b', msg))
    
    # Check for polite request wrappers that precede an action verb: 'תוכל ל...', 'אתה יכול ל...', 'אפשר ל...', 'בבקשה ת...'
    is_action_request_wrapper = bool(re.search(r'(?:תוכל|תוכלי|יכול|יכולה|אפשר|בבקשה|נא|רוצה שת|אשמח שת|מבקש שת)\s+(?:ל|ת)?', msg))

    # Action verbs (imperative / infinitive / 1st person action - both masculine & feminine forms):
    complete_verbs = r'(?:תסמן|תסמני|סמן|סמני|לסמן|תסגור|תסגרי|סגור|סגרי|לסגור|תשלים|תשלימי|השלם|השלימי|להשלים|תסיים|תסיימי|סיים|סיימי|לסיים|סיימתי)'
    edit_verbs = r'(?:תשנה|תשני|שנה|שני|לשנות|תעדכן|תעדכני|עדכן|עדכני|לעדכן|תקבע|תקבעי|קבע|קבעי|לקבוע|תגדיר|תגדירי|הגדר|הגדירי|להגדיר|תשייך|תשייכי|שייך|שייכי|לשייך|תקצה|תקצי|הקצה|הקצי|להקצות)'
    delete_verbs = r'(?:תמחק|תמחקי|מחק|מחקי|למחוק|תסיר|תסירי|הסר|הסירי|להסיר|תבטל|תבטלי|בטל|בטלי|לבטל)'
    archive_verbs = r'(?:תארכב|תארכבי|ארכב|ארכבי|לארכב|תשחזר|תשחזרי|שחזר|שחזרי|לשחזר|העבר\s+לארכיון|העבירי\s+לארכיון|תעביר\s+לארכיון|תעבירי\s+לארכיון|להעביר\s+לארכיון|שים\s+בארכיון|שימי\s+בארכיון|תשים\s+בארכיון|תשימי\s+בארכיון|לשים\s+בארכיון|שלח\s+לארכיון|שלחי\s+לארכיון|תשלח\s+לארכיון|תשלחי\s+לארכיון|שחזר\s+מהארכיון|שחזרי\s+מהארכיון|תשחזר\s+מהארכיון|תשחזרי\s+מהארכיון)'
    move_verbs = r'(?:תעביר|תעבירי|העבר|העבירי|להעביר)'
    date_verbs = r'(?:תדחה|תדחי|דחה|דחי|לדחות|תזיז|תזיזי|הזז|הזיזי|להזיז|תקדים|תקדימי|הקדם|הקדימי|להקדים|תאריך|תאריכי|הארך|האריכי|להאריך)'
    add_to_entity_pattern = r'(?:הוסף|הוסיפי|תוסיף|תוסיפי|להוסיף|צרף|צרפי|תצרף|תצרפי|לצרף)\b.*?\b(?:למשימ|לפרויקט)'
    status_direct_pattern = r'(?:^|\b)(?:משימה\s+)?#?\d+\s+(?:ל|ב|למצב\s+)?(?:תהליך|בתהליך|ביצוע|בביצוע|הושלם|הושלמה|בוצע|בוצעה|מעוכב|מעוכבת|עיכוב|טרם\s+החל)(?:\b|$)'

    any_action_verb = rf'(?:{complete_verbs}|{edit_verbs}|{delete_verbs}|{archive_verbs}|{move_verbs}|{date_verbs})'
    passive_status_actions = r'(?:^|\b)(?:היא\s+הושלמה|זה\s+הושלם|זה\s+בוצע|המשימה\s+הושלמה|סמן\s+כ?הושלם|סמן\s+כ?בוצע)(?:\b|$)'

    if is_inquiry_starter:
        if is_action_request_wrapper and (re.search(any_action_verb, msg) or re.search(add_to_entity_pattern, msg)):
            if not re.search(r'^(?:למה|מדוע|מי)\s+(?:מחקת|שינית|עדכנת|העברת)', msg):
                return True
        return False

    if is_view_starter:
        return False

    if re.search(add_to_entity_pattern, msg):
        return True

    if re.search(status_direct_pattern, msg):
        return True

    if re.search(any_action_verb, msg):
        return True

    if re.search(passive_status_actions, msg):
        if '?' in msg or 'האם' in msg:
            return False
        return True

    return False

def is_user_requesting_creation(user_msg):
    """Determines if the user's message is requesting creation of a new entity."""
    if not user_msg:
        return False
    msg = str(user_msg).strip().lower()
    
    is_inquiry_starter = bool(re.search(r'^(?:מה|מהם|מהן|מי\s+(?!תוכל|יכול)|איזה|איזו|אילו|כמה|למה|מדוע|איפה|היכן|מתי|האם|האם\s+יש|יש\s+משימות|רשימת|רשימה)\b', msg))
    is_view_starter = bool(re.search(r'^(?:תראה|הראה|להראות|הצג|תציג|להציג|פרט|תפרט|לפרט|ספר|תספר|בדוק|תבדוק|לבדוק|תסכם|סכם|לסכם)\b', msg))
    is_action_request_wrapper = bool(re.search(r'(?:תוכל|תוכלי|יכול|יכולה|אפשר|בבקשה|נא|רוצה שת|אשמח שת|מבקש שת)\s+(?:ל|ת)?', msg))

    create_verbs = r'(?:הוסף|הוסיפי|תוסיף|תוסיפי|להוסיף|צור|צרי|תייצר|תייצרי|ליצור|פתח\s+משימ|פתחי\s+משימ|תפתח\s+משימ|תפתחי\s+משימ|לפתוח\s+משימ|הקם|הקימי|תקים|תקימי|להקים)'

    if is_inquiry_starter:
        if is_action_request_wrapper and re.search(create_verbs, msg):
            return True
        return False

    if is_view_starter:
        return False

    return bool(re.search(create_verbs, msg))

def text_contains_entity(entity_name, text):
    """
    Checks if a token / name / team / member (Hebrew or English) is referenced in text as a distinct word,
    handling common Hebrew clitic prefixes (ל, ב, מ, כ, ה, ו, ש, של, ול, שב, וה) while strictly preventing
    false-positive substring matches like 'שי' matching inside 'משימות' or 'אלי' matching 'אלירן'.
    """
    if not entity_name or not text:
        return False
    entity_clean = entity_name.strip().lower()
    tokens = re.findall(r'[a-zA-Z0-9_\u0590-\u05fe]+', text.lower())
    for tok in tokens:
        if tok == entity_clean:
            return True
        if len(tok) == len(entity_clean) + 1 and tok[0] in 'לבמכהוש' and tok[1:] == entity_clean:
            return True
        if len(tok) == len(entity_clean) + 2 and tok[:2] in ['ול', 'וב', 'ומ', 'שב', 'של', 'כש', 'וה', 'מה'] and tok[2:] == entity_clean:
            return True
    return False

def get_team_tasks_query_info(user_msg, ctx=None):
    """
    Checks if user is asking for the tasks of a specific team,
    e.g. 'איזה משימות פתוחות יש לצוות DEVOPS', 'מה המשימות של צוות דבאופס', 'משימות לצוות סיסטם'.
    Returns (team_dict, matching_tasks, is_open_only, is_count_query, all_team_tasks) or None.
    """
    if not user_msg:
        return None
        
    msg = str(user_msg).strip().lower()
    
    is_inquiry = bool(
        re.search(r'(?:מה|מהם|איזה|איזו|אילו|כמה|כמות|מספר|רשימת|הצג|תראה|פרט|יש|של)\s+(?:ה)?משימות', msg) or 
        re.search(r'משימות\s+(?:של|ל|ב)', msg) or 
        re.search(r'(?:מה|כמה)\s+(?:פתוח|פתוחות|יש)\s+ל', msg) or
        ('צוות' in msg and ('משימ' in msg or 'פתוח' in msg or 'פתוחות' in msg))
    )
    if not is_inquiry:
        return None

    if not ctx:
        from ai_context import build_system_context
        ctx = build_system_context()

    teams = ctx.get('teams', [])
    found_team = None

    for t in teams:
        name_he = t.get('name_he', '')
        name_en = t.get('name_en', '')
        if (name_he and text_contains_entity(name_he, msg)) or (name_en and text_contains_entity(name_en, msg)):
            found_team = t
            break

    if not found_team:
        return None

    is_open_only = bool(re.search(r'(?:\b(?:פתוח|פתוחה|פתוחות|פתוחים|open|פעיל|פעילה|פעילות|פעילים)\b|הכל\s+למעט\s+הושלם|למעט\s+הושלם|לא\s+הושלמ)', msg))
    is_count_query = bool(re.search(r'^(?:כמה|מה\s+מספר|מספר|כמות)\b', msg))

    all_tasks = ctx.get('tasks', [])
    
    team_member_ens = set(m['name_en'].strip().lower() for m in found_team.get('members', []) if m.get('name_en'))
    
    team_proj_names = set()
    for p in ctx.get('projects', []):
        p_team_ids = [pt['id'] for pt in p.get('teams', [])]
        if found_team['id'] in p_team_ids:
            team_proj_names.add(p.get('name', '').strip())

    matching = []
    for t in all_tasks:
        t_mems = [m.strip().lower() for m in t.get('members', []) if m.strip()]
        belongs = False
        if t.get('team_id') == found_team['id']:
            belongs = True
        elif any(m in team_member_ens for m in t_mems):
            belongs = True
        elif t.get('project') in team_proj_names:
            belongs = True

        if belongs:
            matching.append(t)

    all_team_tasks = list(matching)
    if is_open_only:
        matching = [t for t in matching if t.get('status') != 'status-done']

    return found_team, matching, is_open_only, is_count_query, all_team_tasks

def format_team_tasks_summary(team_obj, tasks, is_open_only=False, is_count_query=False, all_team_tasks=None, members_lookup=None):
    """
    Formats a team's tasks into a clean, human-friendly Hebrew summary without IDs or technical jargon.
    """
    team_name = f"{team_obj['name_he']} ({team_obj['name_en']})"
    status_map_he = {
        'status-inprogress': 'בתהליך',
        'status-done': 'הושלם',
        'status-delayed': 'מעוכב',
        'status-notstarted': 'טרם החל'
    }
    priority_map_he = {
        'high': 'גבוהה',
        'medium': 'בינונית',
        'low': 'נמוכה',
        'none': 'ללא'
    }

    if not tasks:
        if is_open_only:
            done_count = len([t for t in (all_team_tasks or []) if t.get('status') == 'status-done'])
            if done_count > 0:
                return f"אין לצוות {team_name} משימות פתוחות כרגע (כל {done_count} המשימות של הצוות הושלמו)."
            return f"אין לצוות {team_name} משימות פתוחות כרגע."
        return f"לא נמצאו משימות פעילות עבור צוות {team_name}."

    if is_count_query:
        heading = f"לצוות {team_name} יש כרגע **{len(tasks)}** משימות פתוחות:" if is_open_only else f"לצוות {team_name} יש כרגע **{len(tasks)}** משימות:"
    else:
        heading = f"**משימות פתוחות של צוות {team_name} ({len(tasks)} משימות):**" if is_open_only else f"**משימות של צוות {team_name} ({len(tasks)} משימות):**"

    lines = [heading]
    for t in tasks:
        st = status_map_he.get(t.get('status'), t.get('status', ''))
        prio = priority_map_he.get(t.get('priority'), t.get('priority', ''))
        proj = t.get('project', '')
        title = t.get('task', '')
        raw_m = t.get('members', [])
        if members_lookup:
            m_list = [members_lookup.get(m.lower().strip(), m) for m in raw_m if m and m.strip()]
        else:
            m_list = [m.strip() for m in raw_m if m and m.strip()]
        m_str = f", משויך: {', '.join(m_list)}" if m_list else ""
        lines.append(f"• **#{t.get('id')} [{proj}]:** {title} (סטטוס: {st}, עדיפות: {prio}{m_str})")

    return "\n".join(lines)

def get_member_tasks_query_info(user_msg, ctx=None):
    """
    Checks if user is asking for the tasks of a specific team member,
    e.g. 'כמה משימות פתוחות יש לנועם', 'מה המשימות של אלעד', 'איזה משימות יש לאלירן'.
    Returns (member_name_he, matching_tasks, is_open_only, is_count_query, all_member_tasks) or None.
    """
    if not user_msg:
        return None
    
    msg = str(user_msg).strip().lower()
    
    # If the user specifically asks for a team (contains 'צוות'), defer to team query
    if 'צוות' in msg:
        return None

    is_inquiry = bool(
        re.search(r'(?:מה|מהם|איזה|איזו|אילו|כמה|כמות|מספר|רשימת|הצג|תראה|פרט|יש|של)\s+(?:ה)?משימות', msg) or 
        re.search(r'משימות\s+(?:של|ל|ב)', msg) or 
        re.search(r'(?:מה|כמה)\s+(?:פתוח|פתוחות|יש)\s+ל', msg) or
        re.search(r'\bמשימות\b', msg)
    )
    if not is_inquiry:
        return None

    if not ctx:
        from ai_context import build_system_context
        ctx = build_system_context()

    members_lookup = ctx.get('members_lookup', {})
    all_tasks = ctx.get('tasks', [])

    found_member_he = None
    for name_key, alt_name in members_lookup.items():
        if text_contains_entity(name_key, msg):
            found_member_he = name_key if re.search(r'[\u0590-\u05fe]', name_key) else alt_name
            break

    if not found_member_he:
        for t in ctx.get('teams', []):
            for m in t.get('members', []):
                if text_contains_entity(m['name_he'], msg) or text_contains_entity(m['name_en'], msg):
                    found_member_he = m['name_he']
                    break
            if found_member_he:
                break

    if not found_member_he:
        return None

    is_open_only = bool(re.search(r'(?:\b(?:פתוח|פתוחה|פתוחות|פתוחים|open|פעיל|פעילה|פעילות|פעילים)\b|הכל\s+למעט\s+הושלם|למעט\s+הושלם|לא\s+הושלמ)', msg))
    is_count_query = bool(re.search(r'^(?:כמה|מה\s+מספר|מספר|כמות)\b', msg))

    matching = []
    for t in all_tasks:
        t_members = t.get('members', [])
        m_he = [members_lookup.get(m.lower().strip(), m) for m in t_members]
        if any(found_member_he.lower() in m.lower() for m in m_he):
            matching.append(t)

    all_member_tasks = list(matching)
    if is_open_only:
        matching = [t for t in matching if t.get('status') != 'status-done']

    return found_member_he, matching, is_open_only, is_count_query, all_member_tasks

def format_member_tasks_summary(member_name, tasks, is_open_only=False, is_count_query=False, all_member_tasks=None):
    """
    Formats a member's tasks into a neat, human-friendly Hebrew summary without IDs or technical jargon.
    Excludes completed tasks if is_open_only is True!
    """
    status_map_he = {
        'status-inprogress': 'בתהליך',
        'status-done': 'הושלם',
        'status-delayed': 'מעוכב',
        'status-notstarted': 'טרם החל'
    }
    priority_map_he = {
        'high': 'גבוהה',
        'medium': 'בינונית',
        'low': 'נמוכה',
        'none': 'ללא'
    }

    if not tasks:
        if is_open_only:
            done_tasks = [t for t in (all_member_tasks or []) if t.get('status') == 'status-done']
            if done_tasks:
                first_done = done_tasks[0]
                return f"אין ל{member_name} משימות פתוחות כרגע. המשימה המשויכת אליו (#{first_done.get('id')} [{first_done.get('project')}]: {first_done.get('task')}) כבר הושלמה."
            return f"אין ל{member_name} משימות פתוחות כרגע."
        return f"לא נמצאו משימות פעילות המשויכות ל{member_name}."

    if is_count_query:
        heading = f"ל{member_name} יש כרגע **{len(tasks)}** משימות פתוחות:" if is_open_only else f"ל{member_name} יש כרגע **{len(tasks)}** משימות:"
    else:
        heading = f"**משימות פתוחות המשויכות ל{member_name} ({len(tasks)} משימות):**" if is_open_only else f"**משימות המשויכות ל{member_name} ({len(tasks)} משימות):**"

    lines = [heading]
    for t in tasks:
        st = status_map_he.get(t.get('status'), t.get('status', ''))
        prio = priority_map_he.get(t.get('priority'), t.get('priority', ''))
        proj = t.get('project', '')
        title = t.get('task', '')
        lines.append(f"• **#{t.get('id')} [{proj}]:** {title} (סטטוס: {st}, עדיפות: {prio})")

    return "\n".join(lines)

def filter_hallucinated_actions(actions, user_msg, history=None):
    """
    Validates that any mutating action on existing tasks or projects was actually
    requested by the user and referenced in the conversation context. Drops actions where:
    1. The user only asked an informational query (e.g. 'מה המשימות של אלירן') and did not request mutation.
    2. The model arbitrarily picked a random task or project that was not referenced.
    """
    if not actions:
        return []

    is_mutating = is_user_requesting_mutation(user_msg)
    is_creating = is_user_requesting_creation(user_msg)

    valid_actions = []
    for act in actions:
        action_name = act.get('action')
        params = act.get('params', {})

        # Read-only actions are always safe
        if action_name in ['list_tasks', 'get_tasks', 'search_tasks', 'list_projects', 'get_projects', 'search_projects']:
            valid_actions.append(act)
            continue

        # Creation actions: require user intent to create
        if action_name in ['create_task', 'create_project', 'create_team', 'create_member', 'create_special_day']:
            if is_creating:
                valid_actions.append(act)
            else:
                logger.warning(f"[Action Filter] Dropped creation action without user creation intent: {act} for user_msg: '{user_msg}'")
            continue

        # If user did not request any mutation, drop all mutating actions!
        if not is_mutating:
            logger.warning(f"[Action Filter] Dropped mutating action '{action_name}' because user query is informational/non-mutating: '{user_msg}'")
            continue

        # Task mutations: require user intent AND context reference
        if action_name in ['edit_task', 'delete_task', 'archive_task', 'unarchive_task']:
            task = resolve_task(params)
            if task and is_task_referenced_in_context(task, user_msg, history):
                params['id'] = task.id
                valid_actions.append(act)
            else:
                logger.warning(f"[Action Filter] Dropped unreferenced/hallucinated task action: {act}")
            continue

        # Project mutations: require user intent AND context reference
        if action_name in ['edit_project', 'delete_project', 'archive_project', 'unarchive_project', 'update_project_team', 'add_project_team', 'add_team_to_project', 'assign_team_to_project', 'update_project']:
            proj_val = params.get('id') or params.get('project_id') or params.get('name') or params.get('project_name') or params.get('project')
            project = resolve_project(proj_val)
            if project and is_project_referenced_in_context(project, user_msg, history):
                valid_actions.append(act)
            else:
                logger.warning(f"[Action Filter] Dropped unreferenced/hallucinated project action: {act}")
            continue

        # Team / Member / Special Day mutations
        if action_name in ['edit_team', 'delete_team', 'delete_member', 'delete_special_day']:
            if is_mutating:
                valid_actions.append(act)
            else:
                logger.warning(f"[Action Filter] Dropped team/member mutating action: {act}")
            continue

        valid_actions.append(act)

    return valid_actions

def resolve_project_from_context(user_msg, history=None):
    """Finds a project referenced in user message or recent history."""
    user_str = str(user_msg or '').strip().lower()
    for p in Project.query.all():
        if p.name.lower() in user_str:
            return p
    if history:
        for h in reversed(history):
            content = h.get('content', '').lower()
            for p in Project.query.all():
                if p.name.lower() in content:
                    return p
    return None

def find_target_task_in_context(user_msg, ai_reply='', history=None):
    """
    Finds the target Task object from user message, AI reply, or recent conversation history.
    """
    user_str = str(user_msg or '').strip()
    ai_str = str(ai_reply or '').strip()

    # 1. Direct ID in user message: e.g. #56, משימה 56, המשימה 82, or standalone 56
    user_ids = re.findall(r'#(\d+)', user_str)
    if not user_ids:
        user_ids = re.findall(r'(?:ה)?משימה\s+(?:מספר\s+)?#?(\d+)', user_str)
    if not user_ids and re.search(r'\b\d+\b', user_str):
        user_ids = re.findall(r'\b\d+\b', user_str)

    for tid in user_ids:
        try:
            t = db.session.get(Task, int(tid))
            if t:
                return t
        except Exception:
            pass

    # 2. Check title or keywords in user message
    t = resolve_task({'title': user_str})
    if t and is_task_referenced_in_context(t, user_str, history):
        return t

    # 3. Check for task ID in AI reply (when model mentioned the task in its output)
    if ai_str:
        ai_ids = re.findall(r'#(\d+)', ai_str)
        if not ai_ids:
            ai_ids = re.findall(r'משימה\s+(?:מספר\s+)?(\d+)', ai_str)
        for tid in ai_ids:
            try:
                t = db.session.get(Task, int(tid))
                if t and is_task_referenced_in_context(t, user_str, history):
                    return t
            except Exception:
                pass

    # 4. Check ordinal words in user message ("ראשונה", "שנייה", "אחרונה")
    if history:
        for ord_word, idx in [('ראשונה', 0), ('הראשונה', 0), ('שנייה', 1), ('השנייה', 1), ('שלישית', 2), ('השלישית', 2), ('אחרונה', -1), ('האחרונה', -1)]:
            if ord_word in user_str.lower():
                for h in reversed(history):
                    if h.get('role') == 'assistant':
                        ids = re.findall(r'#(\d+)', h.get('content', ''))
                        if ids and abs(idx) < len(ids):
                            try:
                                t = db.session.get(Task, int(ids[idx]))
                                if t:
                                    return t
                            except Exception:
                                pass
                break

    # 5. Check recent conversation history (most recent assistant/user messages first)
    if history:
        for h in reversed(history):
            content = h.get('content', '')
            # Look for #123
            ids = re.findall(r'#(\d+)', content)
            if ids:
                for tid in ids:
                    try:
                        t = db.session.get(Task, int(tid))
                        if t:
                            return t
                    except Exception:
                        pass
            # Look for משימה 123
            m_ids = re.findall(r'משימה\s+(?:מספר\s+)?(\d+)', content)
            if m_ids:
                for tid in m_ids:
                    try:
                        t = db.session.get(Task, int(tid))
                        if t:
                            return t
                    except Exception:
                        pass
            # Look for [Project] Task in history
            brackets_match = re.findall(r'\[([^\]]+)\]\s*([^\n|•\-]+)', content)
            for p_name, t_name in brackets_match:
                t_cand = resolve_task({'task': t_name.strip(), 'project': p_name.strip()})
                if t_cand:
                    return t_cand

    return None

def detect_fallback_action(user_msg, ai_reply, history=None):
    """
    Intelligently detects user action intent when the AI failed to emit a valid JSON action block.
    Supports:
    - Status updates
    - Delete task / project
    - Archive task / project
    - Unarchive task / project
    - Create task
    - Create project
    - Multi-turn follow up
    
    CRITICAL: Returns None if user message is an informational query.
    """
    if not user_msg or not str(user_msg).strip():
        return None

    user_msg_clean = str(user_msg).strip().lower()

    # Pure informational questions check
    query_starters = [
        'איזה', 'איזו', 'אילו', 'מה ה', 'מהם', 'מהן', 'מי ה', 'מי הם', 'כמה', 'האם',
        'ספר לי', 'הצג', 'תציג', 'תראה לי', 'פרט', 'רשום', 'תספר', 'show', 'what', 'which', 'who', 'list'
    ]
    is_query = any(user_msg_clean.startswith(q) for q in query_starters) or user_msg_clean.endswith('?')
    action_verbs = [
        'שנה', 'תשנה', 'שני', 'תשני', 'לשנות',
        'עדכן', 'תעדכן', 'עדכני', 'תעדכני', 'לעדכן',
        'מחק', 'תמחק', 'מחקי', 'תמחקי', 'למחוק',
        'להסיר', 'הסר', 'הסירי', 'תסיר', 'תסירי',
        'העבר', 'תעביר', 'העבירי', 'תעבירי', 'להעביר',
        'ארכב', 'תארכב', 'ארכבי', 'תארכבי', 'לארכב',
        'שחזר', 'תשחזר', 'שחזרי', 'תשחזרי', 'לשחזר',
        'הוסף', 'תוסיף', 'הוסיפי', 'תוסיפי', 'להוסיף',
        'צור', 'צרי', 'תייצר', 'תייצרי', 'ליצור',
        'פתח', 'פתחי', 'תפתח', 'תפתחי', 'לפתוח',
        'הפוך', 'הפכי', 'תהפוך', 'תהפכי', 'להפוך',
        'שים', 'שימי', 'תשים', 'תשימי', 'לשים',
        'סמן', 'סמני', 'תסמן', 'תסמני', 'לסמן', 'נסמן',
        'השלם', 'השלימי', 'תושלם', 'תשלים', 'תשלימי', 'להשלים', 'הושלם', 'הושלמה',
        'סגור', 'סגרי', 'תסגור', 'תסגרי', 'לסגור', 'נסגר', 'נסגרה',
        'סיים', 'סיימי', 'תסיים', 'תסיימי', 'לסיים', 'סיימתי',
        'קבע', 'קבעי', 'תקבע', 'תקבעי', 'לקבוע',
        'הגדר', 'הגדירי', 'תגדיר', 'תגדירי', 'להגדיר',
        'בצע', 'בצעי', 'תבצע', 'תבצעי', 'לבצע', 'בוצע', 'בוצעה',
        'עשה', 'עשי', 'תעשה', 'תעשי', 'לעשות',
        'mark', 'set', 'close', 'finish', 'complete', 'done', 'update', 'change'
    ]
    has_action = any(v in user_msg_clean for v in action_verbs)

    if is_query and not has_action:
        return None

    # Check for multi-turn intent resolution
    inherited_intent = None
    if not has_action and history:
        for h in reversed(history):
            if h.get('role') == 'user':
                prev_text = h.get('content', '').lower()
                if any(v in prev_text for v in action_verbs):
                    inherited_intent = prev_text
                    break

    action_context = f"{user_msg_clean} {inherited_intent or ''}"

    # 1. DELETE INTENT
    if any(k in action_context for k in ['מחק', 'תמחק', 'מחקי', 'תמחקי', 'למחוק', 'הסר', 'הסירי', 'תסיר', 'תסירי', 'להסיר', 'delete', 'remove']):
        if 'פרויקט' in user_msg_clean:
            p = resolve_project_from_context(user_msg, history)
            if p:
                return [{'action': 'delete_project', 'params': {'id': p.id, 'name': p.name}}]
        t = find_target_task_in_context(user_msg, ai_reply, history)
        if t and is_task_referenced_in_context(t, user_msg, history):
            return [{'action': 'delete_task', 'params': {'id': t.id, 'task': t.task}}]

    # 2. UNARCHIVE INTENT
    if any(k in action_context for k in ['שחזר', 'תשחזר', 'שחזרי', 'תשחזרי', 'לשחזר', 'החזר מהארכיון', 'החזירי מהארכיון', 'תחזיר מהארכיון', 'תחזירי מהארכיון', 'להחזיר מהארכיון', 'unarchive', 'restore']):
        if 'פרויקט' in user_msg_clean:
            p = resolve_project_from_context(user_msg, history)
            if p:
                return [{'action': 'unarchive_project', 'params': {'id': p.id, 'name': p.name, 'is_archived': False}}]
        t = find_target_task_in_context(user_msg, ai_reply, history)
        if t and is_task_referenced_in_context(t, user_msg, history):
            return [{'action': 'unarchive_task', 'params': {'id': t.id, 'task': t.task, 'is_archived': False}}]

    # 3. ARCHIVE INTENT
    archive_in_user = any(k in action_context for k in ['ארכיון', 'לארכיון', 'ארכב', 'תארכב', 'ארכבי', 'תארכבי', 'לארכב', 'archive']) and not any(k in action_context for k in ['שחזר', 'תשחזר', 'שחזרי', 'תשחזרי', 'unarchive'])
    archive_in_ai = ai_reply and any(k in ai_reply.lower() for k in ['ארכיב', 'הועברה לארכיון', 'הועבר לארכיון', 'לארכיון']) and not any(k in ai_reply.lower() for k in ['שחזר', 'unarchive'])
    if archive_in_user or archive_in_ai:
        if 'פרויקט' in user_msg_clean:
            p = resolve_project_from_context(user_msg, history)
            if p:
                return [{'action': 'archive_project', 'params': {'id': p.id, 'name': p.name, 'is_archived': True}}]
        t = find_target_task_in_context(user_msg, ai_reply, history)
        if t and is_task_referenced_in_context(t, user_msg, history):
            return [{'action': 'archive_task', 'params': {'id': t.id, 'task': t.task, 'is_archived': True}}]

    # 4. STATUS UPDATE INTENT
    target_status = None
    status_keywords = {
        'status-inprogress': ['בתהליך', 'תהליך', 'בביצוע', 'בעבודה', 'in progress', 'inprogress', 'in-progress', 'החל', 'התחיל'],
        'status-done': ['הושלם', 'הושלמה', 'הסתיים', 'הסתיימה', 'בוצע', 'בוצעה', 'סיימתי', 'גמור', 'גמורה', 'done', 'completed', 'נסגר', 'נסגרה', 'סגור', 'סגורה', 'השלמתי', 'closed', 'finished'],
        'status-delayed': ['מעוכב', 'מעוכבת', 'עיכוב', 'ממתין', 'ממתינה', 'תקוע', 'תקועה', 'delayed', 'hold'],
        'status-notstarted': ['טרם החל', 'לא החל', 'לא התחיל', 'not started', 'notstarted', 'חדש', 'חדשה', 'פתוח', 'פתוחה']
    }
    for st, keywords in status_keywords.items():
        if any(kw in action_context for kw in keywords):
            target_status = st
            break

    # If verb is mark/close/complete and no other status is given, default to status-done
    if not target_status and any(k in action_context for k in ['סמן', 'סמני', 'תסמן', 'תסמני', 'לסמן', 'סגור', 'סגרי', 'תסגור', 'תסגרי', 'לסגור', 'סיים', 'סיימי', 'תסיים', 'תסיימי', 'לסיים', 'השלם', 'השלימי', 'תשלים', 'תשלימי', 'להשלים', 'סיימתי', 'mark', 'close', 'complete', 'check']):
        target_status = 'status-done'

    # If AI reply claims a status and user had action intent
    if not target_status and ai_reply and (has_action or inherited_intent):
        ai_lower = ai_reply.lower()
        for st, keywords in status_keywords.items():
            if any(f"סטטוס: {kw}" in ai_lower or f"סטטוס:{kw}" in ai_lower or f"סטטוס {kw}" in ai_lower or f"status: {kw}" in ai_lower for kw in keywords):
                target_status = st
                break

    has_target_task_mention = bool(re.search(r'(?:^|\b)(?:משימה\s+)?#?\d+', user_msg_clean))
    if target_status and (has_action or inherited_intent or has_target_task_mention or any(p in user_msg_clean for p in ['אותה', 'אותו', 'זה', 'את זה', 'אותם'])):
        t = find_target_task_in_context(user_msg, ai_reply, history)
        if t and is_task_referenced_in_context(t, user_msg, history):
            return [{
                'action': 'edit_task',
                'params': {
                    'id': t.id,
                    'status': target_status,
                    'task': t.task
                }
            }]

    # 5. CREATE TASK INTENT
    if any(k in user_msg_clean for k in ['תוסיף משימה', 'תוסיפי משימה', 'צור משימה', 'צרי משימה', 'הוסף משימה', 'הוסיפי משימה', 'פתח משימה', 'פתחי משימה', 'תפתח משימה', 'תפתחי משימה', 'add task', 'create task']):
        t_clean = re.sub(r'^(?:תוסיף|תוסיפי|צור|צרי|הוסף|הוסיפי|פתח|פתחי|תפתח|תפתחי)\s+משימה\s+(?:חדשה\s+)?', '', user_msg, flags=re.IGNORECASE).strip()
        prio = 'none'
        if 'גבוהה' in t_clean or 'דחוף' in t_clean: prio = 'high'
        elif 'בינונית' in t_clean: prio = 'medium'
        elif 'נמוכה' in t_clean: prio = 'low'
        
        p_name = None
        proj_match = re.search(r'\b(?:בפרויקט|לפרויקט)\s+([^\s]+(?:\s+[^\s]+){0,3})', t_clean)
        if proj_match:
            p_cand = proj_match.group(1)
            p_cand = re.split(r'\s+(?:עבור|ל-|בעדיפות|בסטטוס)\b', p_cand)[0].strip()
            p_obj = resolve_project(p_cand)
            if p_obj: p_name = p_obj.name
        
        member = None
        m_match = re.search(r'\b(?:עבור|לחבר|למשתמש)\s+([^\s]+)', t_clean)
        if m_match:
            member = m_match.group(1).strip()
            
        title = re.split(r'\s+(?:בפרויקט|לפרויקט|עבור|בעדיפות)\b', t_clean)[0].strip()
        if title:
            return [{
                'action': 'create_task',
                'params': {
                    'task': title,
                    'project': p_name,
                    'members': [member] if member else [],
                    'priority': prio,
                    'status': 'status-notstarted'
                }
            }]

    # 6. CREATE PROJECT INTENT
    if any(k in user_msg_clean for k in ['תוסיף פרויקט', 'תוסיפי פרויקט', 'צור פרויקט', 'צרי פרויקט', 'הוסף פרויקט', 'הוסיפי פרויקט', 'פתח פרויקט', 'פתחי פרויקט', 'תפתח פרויקט', 'תפתחי פרויקט', 'add project', 'create project']):
        p_clean = re.sub(r'^(?:תוסיף|תוסיפי|צור|צרי|הוסף|הוסיפי|פתח|פתחי|תפתח|תפתחי)\s+פרויקט\s+(?:חדש\s+)?(?:בשם\s+)?', '', user_msg, flags=re.IGNORECASE).strip()
        team = None
        team_match = re.search(r'\b(?:לצוות|עבור צוות|בצוות)\s+([^\s]+)', p_clean)
        if team_match:
            team = team_match.group(1).strip()
        p_name = re.split(r'\s+(?:לצוות|עבור צוות|בצוות)\b', p_clean)[0].strip(' "״\'')
        if p_name:
            return [{
                'action': 'create_project',
                'params': {
                    'name': p_name,
                    'teams': [team] if team else []
                }
            }]

    # 7. CREATE MEMBER INTENT
    if any(k in user_msg_clean for k in ['חבר צוות', 'חבר חדש', 'חברה חדשה', 'משתמש חדש', 'משתמשת חדשה', 'create_member', 'add member']):
        if any(k in user_msg_clean for k in ['הוסף', 'הוסיפי', 'תוסיף', 'תוסיפי', 'להוסיף', 'צור', 'צרי', 'תייצר', 'תייצרי', 'ליצור', 'פתח', 'פתחי']):
            name_he = None
            he_match = re.search(r'\bבשם\s+[\'\"״]?([^\s\'\"״()]+)', user_msg)
            if he_match:
                name_he = he_match.group(1).strip()

            name_en = None
            en_match = re.search(r'\(([a-zA-Z0-9_\-\s]+)\)', user_msg)
            if en_match:
                name_en = en_match.group(1).strip().lower()
            elif name_he:
                name_en = name_he.lower()

            team_val = None
            t_match = re.search(r'\b(?:לצוות|בצוות|עבור צוות)\s+([^\s]+)', user_msg)
            if t_match:
                team_val = t_match.group(1).strip()

            if name_he:
                return [{
                    'action': 'create_member',
                    'params': {
                        'name_he': name_he,
                        'name_en': name_en or name_he,
                        'team': team_val
                    }
                }]

    # 8. ADD MEMBER TO TASK INTENT
    add_member_match = re.search(r'(?:תוסיף|תוסיפי|הוסף|הוסיפי|צרף|צרפי|תצרף|תצרפי)\s+את\s+([^\s]+)\s+למשימ', user_msg_clean)
    if add_member_match:
        m_name = add_member_match.group(1).strip()
        t = find_target_task_in_context(user_msg, ai_reply, history)
        if t:
            existing = [x.strip() for x in (t.members or '').split(',') if x.strip()]
            new_m = resolve_member_names([m_name])
            for nm in new_m:
                if nm not in existing:
                    existing.append(nm)
            return [{
                'action': 'edit_task',
                'params': {
                    'id': t.id,
                    'members': existing,
                    'task': t.task
                }
            }]

    # 9. POSTPONE / DATE CHANGE INTENT
    if any(k in action_context for k in ['תדחה', 'תדחי', 'דחה', 'דחי', 'לדחות', 'תזיז', 'תזיזי', 'הזז', 'הזיזי', 'להזיז', 'תקדים', 'תקדימי', 'הקדם', 'הקדימי', 'להקדים']):
        t = find_target_task_in_context(user_msg, ai_reply, history)
        if t and is_task_referenced_in_context(t, user_msg, history):
            date_match = re.search(r'\b(?:ל-|עד\s+)?(\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?|\d{4}-\d{2}-\d{2})\b', user_msg)
            if date_match:
                d_val = parse_date_value(date_match.group(1))
                if d_val:
                    return [{
                        'action': 'edit_task',
                        'params': {
                            'id': t.id,
                            'end_date': d_val.isoformat(),
                            'task': t.task
                        }
                    }]

    return None

detect_fallback_status_update = detect_fallback_action

def format_task_status_summary(task, members_lookup=None):
    """Generates an organized, human-readable Hebrew summary of a task with zero user IDs and zero English statuses."""
    if not task:
        return ""
    status_map_he = {
        'status-inprogress': 'בתהליך',
        'status-done': 'הושלם',
        'status-delayed': 'מעוכב',
        'status-notstarted': 'טרם החל'
    }
    priority_map_he = {
        'high': 'גבוהה',
        'medium': 'בינונית',
        'low': 'נמוכה',
        'none': 'ללא',
        'urgent': 'דחופה',
        'normal': 'רגילה'
    }
    st_he = 'בארכיון' if getattr(task, 'is_archived', False) else status_map_he.get(task.status, task.status)
    p_raw = str(getattr(task, 'priority', '') or 'none').lower().strip()
    prio_he = priority_map_he.get(p_raw, priority_map_he.get(p_raw.replace('priority-', ''), getattr(task, 'priority', 'ללא') or 'ללא'))

    # Members in Hebrew
    members_list = [m.strip() for m in task.members.split(',') if m.strip()] if task.members else []
    if members_lookup:
        members_he = [members_lookup.get(m.lower(), m) for m in members_list]
    else:
        members_he = members_list
    members_str = ', '.join(members_he) if members_he else 'ללא משויך'

    dates = []
    if task.start_date:
        dates.append(f"התחלה: {task.start_date.strftime('%d/%m/%Y')}")
    if task.end_date:
        dates.append(f"יעד: {task.end_date.strftime('%d/%m/%Y')}")
    dates_str = ', '.join(dates) if dates else 'לא הוגדרו תאריכים'

    hours_str = f"{task.estimated_hours} שעות" if task.estimated_hours else 'לא צוין'
    notes_str = task.notes.strip() if task.notes else 'אין הערות'

    return (
        f"**פרטי משימה #{task.id}: {task.task}**\n"
        f"• **פרויקט:** {task.project}\n"
        f"• **סטטוס:** {st_he}\n"
        f"• **עדיפות:** {prio_he}\n"
        f"• **אחראי / משויך:** {members_str}\n"
        f"• **תאריכים:** {dates_str}\n"
        f"• **שעות משוערות:** {hours_str}\n"
        f"• **הערות:** {notes_str}"
    )

def is_task_status_query(user_msg):
    """Detects whether user is querying the status or details of a task."""
    if not user_msg:
        return False
    msg = str(user_msg).strip().lower()
    patterns = [
        r'מה\s+(?:ה)?סטטוס',
        r'מה\s+(?:ה)?מצב\s+של',
        r'מה\s+(?:ה)?מצב\s+ב?משימ',
        r'סטטוס\s+(?:של\s+)?משימ',
        r'מצב\s+(?:של\s+)?משימ',
        r'פרטי\s+(?:ה)?משימ',
        r'תפרט\s+על\s+(?:ה)?משימ',
        r'ספר\s+לי\s+על\s+(?:ה)?משימ',
        r'מי\s+עובד\s+על\s+(?:ה)?משימ',
        r'איפה\s+עומדת\s+(?:ה)?משימ',
        r'באיזה\s+סטטוס\s+(?:ה)?משימ'
    ]
    return any(re.search(pat, msg) for pat in patterns)

def sanitize_ai_reply(text, mutating_successes=None, members_lookup=None):
    """
    Cleanses AI response:
    1. NEVER mention 'בלוק JSON' or 'JSON' in user reply.
    2. NEVER output duplicate success messages (leaves only styled card).
    3. Translate all status codes to natural Hebrew (e.g. status-inprogress -> בתהליך).
    4. Translate all priority codes to Hebrew (high -> גבוהה).
    5. Strip any user IDs / member IDs and replace English usernames with Hebrew names.
    """
    if not text:
        return ""
    clean = str(text)

    # 1. Strip code blocks of JSON completely
    clean = re.sub(r'```(?:json)?\s*\{[\s\S]*?\}\s*```', '', clean).strip()
    clean = re.sub(r'```(?:json)?\s*\[[\s\S]*?\]\s*```', '', clean).strip()
    clean = re.sub(r'```(?:json)?[\s\S]*?```', '', clean).strip()
    clean = re.sub(r'```(?:json)?', '', clean).strip()
    clean = re.sub(r'```', '', clean).strip()

    # Also strip raw unfenced JSON objects/arrays representing actions
    clean = re.sub(r'\{\s*"actions"\s*:\s*\[[\s\S]*?\]\s*\}', '', clean).strip()
    clean = re.sub(r'\{\s*"action"\s*:\s*"[^"]+"[\s\S]*?\}', '', clean).strip()
    clean = re.sub(r'\[\s*\{\s*"action"\s*:\s*"[^"]+"[\s\S]*?\}\s*\]', '', clean).strip()

    # If the remaining text is entirely valid JSON action, clear it
    candidate_json = clean.strip()
    if (candidate_json.startswith('{') and candidate_json.endswith('}')) or (candidate_json.startswith('[') and candidate_json.endswith(']')):
        try:
            pj = json.loads(candidate_json)
            if isinstance(pj, dict) and ('action' in pj or 'actions' in pj):
                clean = ''
            elif isinstance(pj, list) and pj and isinstance(pj[0], dict) and 'action' in pj[0]:
                clean = ''
        except Exception:
            pass

    # 2. Strip any sentences or lines referencing JSON / בלוק JSON
    clean = re.sub(r'(?i)[^\n.]*(?:בלוק|קוד|פקודת|מבנה|פורמט)?\s*(?:ה-)?(?:JSON|json)[^\n.]*(?:\.|\n|$)', '', clean)
    clean = re.sub(r'(?i)(?:הנה|להלן|הוספתי|צירפתי|שלחתי|לפי|פלוט)\s+(?:את\s+)?(?:בלוק\s+)?(?:ה-)?(?:JSON|json)[^:\n]*[:\s]*', '', clean)
    clean = re.sub(r'(?i)\b(?:בלוק\s+(?:ה-)?json|פקודת\s+json|קוד\s+json|מבנה\s+json)\b', '', clean)
    clean = re.sub(r'(?i)\b(?:JSON|json)\b', '', clean)

    # 3. Strip system prompt regurgitation
    clean = re.split(r'(?:כללים מחייבים לביצוע פעולות|\bזכור את כללי הביצוע|\bכללי הביצוע של פעולות|\bכללי ברזל לתקשורת)', clean)[0].strip()

    # 4. Status translation to Hebrew
    status_replacements = [
        (r'\bstatus-inprogress\b', 'בתהליך'),
        (r'\bstatus-done\b', 'הושלם'),
        (r'\bstatus-delayed\b', 'מעוכב'),
        (r'\bstatus-notstarted\b', 'טרם החל'),
        (r'\binprogress\b', 'בתהליך'),
        (r'\bin-progress\b', 'בתהליך'),
        (r'\bnotstarted\b', 'טרם החל'),
        (r'\bnot-started\b', 'טרם החל'),
    ]
    for pat, rep in status_replacements:
        clean = re.sub(pat, rep, clean, flags=re.IGNORECASE)

    # 5. Priority translation to Hebrew
    priority_translations = {
        'high': 'גבוהה',
        'medium': 'בינונית',
        'low': 'נמוכה',
        'urgent': 'דחופה',
        'normal': 'רגילה',
        'none': 'ללא'
    }
    for eng, heb in priority_translations.items():
        clean = re.sub(rf'(?i)\b(?:עדיפות|priority)\s*:\s*{eng}\b:?', f'עדיפות: {heb}', clean)
        clean = re.sub(rf'(?i)\b(?:עדיפות|priority)\s*:\s*{heb}\b:?', f'עדיפות: {heb}', clean)
        clean = re.sub(rf'(?i)\b{eng}\s*:\s*(?:עדיפות|priority)\b', f'עדיפות: {heb}', clean)

    # 6. Task ID duplicate line removal (e.g. "• ID: #77", "• מזהה: 77", "ID: #77")
    clean = re.sub(r'(?mi)^\s*[-•*]?\s*(?:Task\s*)?(?:ID|מזהה|מזהה משימה)\s*:\s*#?\d+\s*$\n?', '', clean)

    # 7. User / Member IDs removal
    clean = re.sub(r'\(?\b(?:User\s*ID|Member\s*ID|מזהה\s*משתמש|מזהה\s*חבר|ID של משתמש|ID של חבר)\s*[:#]?\s*\d+\)?', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\(?\b(?:משתמש|חבר\s+צוות|חבר)\s*(?:ID|מזהה)\s*[:#]?\s*\d+\)?', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\(ID:\s*\d+\)', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\(מזהה:\s*\d+\)', '', clean, flags=re.IGNORECASE)

    # 7. English username translation to Hebrew
    if members_lookup:
        for en_name, he_name in members_lookup.items():
            if en_name.isascii() and he_name != en_name:
                clean = re.sub(rf'\b{re.escape(en_name)}\b', he_name, clean, flags=re.IGNORECASE)

    # 8. Deduplicate mutating success action messages (Leave only the styled card)
    if mutating_successes:
        for act in mutating_successes:
            desc = act.get('description', '')
            if desc:
                clean = clean.replace(f"✅ {desc}", "")
                clean = clean.replace(desc, "")
            tid = act.get('task_id')
            if tid:
                clean = re.sub(rf'^\s*[-•]?\s*עודכנה\s+משימה\s+#?{tid}[^\n]*$', '', clean, flags=re.MULTILINE)
                clean = re.sub(rf'^\s*[-•]?\s*נמחקה\s+משימה\s+#?{tid}[^\n]*$', '', clean, flags=re.MULTILINE)
                clean = re.sub(rf'^\s*[-•]?\s*הועברה\s+לארכיון\s+משימה\s+#?{tid}[^\n]*$', '', clean, flags=re.MULTILINE)
                clean = re.sub(rf'^\s*[-•]?\s*שוחזרה\s+מהארכיון\s+משימה\s+#?{tid}[^\n]*$', '', clean, flags=re.MULTILINE)

        clean = re.sub(r'בוצע בהצלחה:\s*$', '', clean).strip()
        clean = re.sub(r'בוצע בהצלחה\s*$', '', clean).strip()
        clean = re.sub(r'^\s*[-•]\s*$', '', clean, flags=re.MULTILINE).strip()

    # 9. Clean up spacing and empty parentheses
    clean = re.sub(r'\(\s*\)', '', clean)
    clean = re.sub(r'  +', ' ', clean)
    clean = re.sub(r'\n{3,}', '\n\n', clean)
    return clean.strip()

def extract_json_actions(ai_text):
    """Extracts JSON action blocks from the AI response and deduplicates them."""
    if not ai_text:
        return []
    if isinstance(ai_text, dict):
        if 'actions' in ai_text and isinstance(ai_text['actions'], list):
            actions = ai_text['actions']
        elif 'action' in ai_text:
            actions = [ai_text]
        else:
            actions = []
    elif isinstance(ai_text, list):
        actions = ai_text
    else:
        ai_text = str(ai_text)
        fenced_matches = re.findall(r'```(?:json)?\s*([\s\S]*?)\s*```', ai_text)
        candidates = fenced_matches if fenced_matches else [ai_text]

        actions = []
        for block in candidates:
            block = block.strip()
            start_obj = block.find('{')
            start_arr = block.find('[')
            
            start_idx = -1
            if start_obj != -1 and start_arr != -1:
                start_idx = min(start_obj, start_arr)
            elif start_obj != -1:
                start_idx = start_obj
            elif start_arr != -1:
                start_idx = start_arr

            if start_idx == -1:
                continue

            json_str = block[start_idx:]
            try:
                parsed = json.loads(json_str)
                if isinstance(parsed, dict):
                    if 'actions' in parsed and isinstance(parsed['actions'], list):
                        actions.extend(parsed['actions'])
                    elif 'action' in parsed:
                        actions.append(parsed)
                elif isinstance(parsed, list):
                    actions.extend(parsed)
            except Exception:
                end_idx = max(json_str.rfind('}'), json_str.rfind(']'))
                if end_idx != -1:
                    try:
                        parsed = json.loads(json_str[:end_idx+1])
                        if isinstance(parsed, dict):
                            if 'actions' in parsed and isinstance(parsed['actions'], list):
                                actions.extend(parsed['actions'])
                            elif 'action' in parsed:
                                actions.append(parsed)
                        elif isinstance(parsed, list):
                            actions.extend(parsed)
                    except Exception:
                        pass

    # Deduplicate actions
    deduped = []
    seen = set()
    for a in actions:
        if not isinstance(a, dict):
            continue
        act_name = a.get('action') or a.get('name')
        params = a.get('params') or a.get('parameters') or a
        if not act_name:
            continue
        if act_name == 'create_task':
            t_key = str(params.get('task') or params.get('title') or params.get('name') or '').strip().lower()
            p_key = str(params.get('project') or '').strip().lower()
            key = (act_name, t_key, p_key)
        elif act_name in ['edit_task', 'delete_task', 'archive_task', 'unarchive_task']:
            id_key = str(params.get('id') or params.get('task_id') or params.get('task') or '').strip().lower()
            st_key = str(params.get('status') or '').strip().lower()
            key = (act_name, id_key, st_key)
        elif act_name in ['create_project', 'edit_project', 'delete_project', 'archive_project', 'unarchive_project']:
            p_key = str(params.get('name') or params.get('name_he') or params.get('id') or '').strip().lower()
            key = (act_name, p_key)
        else:
            key = (act_name, json.dumps(params, sort_keys=True, ensure_ascii=False))

        if key not in seen:
            seen.add(key)
            deduped.append(a)

    return deduped

def execute_actions(actions):
    """Executes validated actions in the database and returns execution summary."""
    results = []
    refresh_needed = False

    for item in actions:
        if not isinstance(item, dict):
            continue
        action_name = item.get('action') or item.get('name')
        params = item.get('params') or item.get('parameters') or item
        if not action_name:
            continue

        try:
            if action_name == 'create_task':
                res = _action_create_task(params)
                results.append(res)
                if res['status'] == 'success':
                    refresh_needed = True

            elif action_name == 'edit_task':
                res = _action_edit_task(params)
                results.append(res)
                if res['status'] == 'success':
                    refresh_needed = True

            elif action_name == 'delete_task':
                res = _action_delete_task(params)
                results.append(res)
                if res['status'] == 'success':
                    refresh_needed = True

            elif action_name in ['archive_task', 'unarchive_task']:
                is_arch = params['is_archived'] if 'is_archived' in params else (action_name == 'archive_task')
                res = _action_archive_task(params, is_archived=is_arch)
                results.append(res)
                if res['status'] == 'success':
                    refresh_needed = True

            elif action_name == 'create_project':
                res = _action_create_project(params)
                results.append(res)
                if res['status'] == 'success':
                    refresh_needed = True

            elif action_name in ['edit_project', 'update_project', 'update_project_team', 'add_project_team', 'add_team_to_project', 'assign_team_to_project']:
                res = _action_edit_project(params)
                results.append(res)
                if res['status'] == 'success':
                    refresh_needed = True

            elif action_name in ['archive_project', 'unarchive_project']:
                is_arch = params['is_archived'] if 'is_archived' in params else (action_name == 'archive_project')
                res = _action_archive_project(params, is_archived=is_arch)
                results.append(res)
                if res['status'] == 'success':
                    refresh_needed = True

            elif action_name == 'delete_project':
                res = _action_delete_project(params)
                results.append(res)
                if res['status'] == 'success':
                    refresh_needed = True

            elif action_name == 'create_team':
                res = _action_create_team(params)
                results.append(res)
                if res['status'] == 'success':
                    refresh_needed = True

            elif action_name == 'edit_team':
                res = _action_edit_team(params)
                results.append(res)
                if res['status'] == 'success':
                    refresh_needed = True

            elif action_name == 'delete_team':
                res = _action_delete_team(params)
                results.append(res)
                if res['status'] == 'success':
                    refresh_needed = True

            elif action_name == 'create_member':
                res = _action_create_member(params)
                results.append(res)
                if res['status'] == 'success':
                    refresh_needed = True

            elif action_name == 'delete_member':
                res = _action_delete_member(params)
                results.append(res)
                if res['status'] == 'success':
                    refresh_needed = True

            elif action_name == 'create_special_day':
                res = _action_create_special_day(params)
                results.append(res)
                if res['status'] == 'success':
                    refresh_needed = True

            elif action_name == 'delete_special_day':
                res = _action_delete_special_day(params)
                results.append(res)
                if res['status'] == 'success':
                    refresh_needed = True

            elif action_name in ['list_tasks', 'get_tasks', 'search_tasks']:
                res = _action_list_tasks(params)
                results.append(res)

            elif action_name in ['list_projects', 'get_projects', 'search_projects']:
                res = _action_list_projects(params)
                results.append(res)

            else:
                results.append({
                    'action': action_name,
                    'status': 'error',
                    'error': f'פעולה לא מוכרת: {action_name}'
                })
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error executing action {action_name}: {e}")
            results.append({
                'action': action_name,
                'status': 'error',
                'error': f'שגיאה בביצוע {action_name}: {str(e)}'
            })

    return results, refresh_needed

# ================= ACTION IMPLEMENTATIONS =================

def _action_list_tasks(params):
    query = Task.query.filter_by(is_archived=False)
    
    # Filter by status
    status = params.get('status')
    if status:
        status_str = str(status).strip().lower()
        if status_str in ['not-done', 'status-notdone', 'הכל למעט הושלם', 'למעט הושלם', 'לא הושלם']:
            query = query.filter(Task.status != 'status-done')
        else:
            norm_status = normalize_status(status)
            if norm_status:
                query = query.filter_by(status=norm_status)
            
    # Filter by project
    proj_val = params.get('project') or params.get('project_id') or params.get('project_name')
    if proj_val:
        p_obj = resolve_project(proj_val)
        if p_obj:
            query = query.filter((Task.project_id == p_obj.id) | (Task.project == p_obj.name))
            
    # Filter by team
    team_val = params.get('team') or params.get('team_id') or params.get('team_name')
    if team_val:
        clean_t = str(team_val).strip()
        clean_t_no_prefix = re.sub(r'^צוות\s+', '', clean_t).strip()
        t_obj = Team.query.filter(
            (Team.name_he == clean_t) |
            (Team.name_he == clean_t_no_prefix) |
            (Team.name_en == clean_t.lower()) |
            (Team.name_en == clean_t_no_prefix.lower())
        ).first()
        if t_obj:
            p_ids = [p.id for p in t_obj.projects]
            query = query.filter((Task.team_id == t_obj.id) | (Task.project_id.in_(p_ids)))
            
    # Filter by member
    member_val = params.get('member') or params.get('user') or params.get('assigned')
    if member_val:
        m_res = resolve_member_names([member_val])
        if m_res:
            m_en = m_res[0]
            query = query.filter(Task.members.like(f"%{m_en}%"))
            
    tasks = query.order_by(Task.id.desc()).limit(25).all()
    if not tasks:
        return {
            'action': 'list_tasks',
            'status': 'success',
            'description': 'לא נמצאו משימות התואמות את הבקשה.'
        }
        
    status_he = {
        'status-notstarted': 'טרם החל',
        'status-inprogress': 'בתהליך',
        'status-done': 'הושלם',
        'status-delayed': 'מעוכב'
    }
    
    lines = [f"נמצאו {len(tasks)} משימות:"]
    for t in tasks:
        st_text = status_he.get(t.status, t.status)
        mem_text = f" (משויך: {t.members})" if t.members else ""
        lines.append(f"• #{t.id} [{t.project}] {t.task} - סטטוס: {st_text}{mem_text}")
        
    return {
        'action': 'list_tasks',
        'status': 'success',
        'description': "\n".join(lines)
    }

def _action_list_projects(params):
    projects = Project.query.filter_by(is_archived=False).all()
    lines = [f"קיימים {len(projects)} פרויקטים פעילים במערכת:"]
    for p in projects:
        t_names = [t.name_he for t in p.teams]
        t_str = f" (צוותים: {', '.join(t_names)})" if t_names else ""
        lines.append(f"• {p.name}{t_str} - {len(p.tasks)} משימות")
    return {
        'action': 'list_projects',
        'status': 'success',
        'description': "\n".join(lines)
    }

def _action_create_task(params):
    proj_val = params.get('project') or params.get('project_id') or params.get('project_name')
    project_obj = resolve_project(proj_val)
    
    if not project_obj:
        # Create project if not exists
        p_name = str(proj_val).strip() if proj_val else "פרויקט כללי"
        first_team = Team.query.first()
        teams = [first_team] if first_team else []
        project_obj = Project(name=p_name, teams=teams)
        db.session.add(project_obj)
        db.session.flush()

    task_title = params.get('task') or params.get('title') or 'משימה חדשה'
    members_resolved = resolve_member_names(params.get('members'))
    members_str = ','.join(members_resolved)

    # Status & Priority mapping
    status = params.get('status', 'status-notstarted')
    status_map = {
        'notstarted': 'status-notstarted',
        'inprogress': 'status-inprogress',
        'in_progress': 'status-inprogress',
        'done': 'status-done',
        'delayed': 'status-delayed',
        'טרם החל': 'status-notstarted',
        'בתהליך': 'status-inprogress',
        'הושלם': 'status-done',
        'מעוכב': 'status-delayed'
    }
    status = status_map.get(status, status)

    priority = params.get('priority', 'none').lower()
    priority_map = {
        'גבוהה': 'high',
        'בינונית': 'medium',
        'נמוכה': 'low',
        'ללא': 'none'
    }
    priority = priority_map.get(priority, priority)
    if priority not in ['high', 'medium', 'low', 'none']:
        priority = 'none'

    start_date = parse_date_value(params.get('start_date'))
    end_date = parse_date_value(params.get('end_date'))
    
    est_hours = params.get('estimated_hours')
    try:
        est_hours = float(est_hours) if est_hours is not None else None
    except (ValueError, TypeError):
        est_hours = None

    team_id = params.get('team_id')
    if not team_id and project_obj.teams:
        team_id = project_obj.teams[0].id

    new_task = Task(
        project_id=project_obj.id,
        project=project_obj.name,
        task=task_title,
        members=members_str,
        status=status,
        priority=priority,
        notes=params.get('notes', ''),
        team_id=team_id,
        start_date=start_date,
        end_date=end_date,
        estimated_hours=est_hours
    )
    db.session.add(new_task)
    db.session.commit()

    return {
        'action': 'create_task',
        'status': 'success',
        'task_id': new_task.id,
        'description': f'נוצרה משימה חדשה: "{task_title}" בפרויקט "{project_obj.name}"'
    }

def _action_edit_task(params):
    task = resolve_task(params)
    if not task:
        return {'action': 'edit_task', 'status': 'error', 'error': 'משימה לעריכה לא נמצאה'}

    if 'project' in params or 'project_id' in params:
        proj_val = params.get('project') or params.get('project_id')
        p_obj = resolve_project(proj_val)
        if p_obj:
            task.project_id = p_obj.id
            task.project = p_obj.name

    if 'new_task' in params:
        task.task = params['new_task'].strip()
    elif 'new_title' in params:
        task.task = params['new_title'].strip()
    elif 'task' in params and 'id' in params and str(params['id']).isdigit():
        task.task = params['task'].strip()

    if 'add_member' in params or 'add_members' in params:
        add_res = resolve_member_names(params.get('add_member') or params.get('add_members'))
        current_members = [m.strip() for m in (task.members or '').split(',') if m.strip()]
        for m in add_res:
            if m not in current_members:
                current_members.append(m)
        task.members = ','.join(current_members)
    elif 'members' in params:
        members_res = resolve_member_names(params['members'])
        task.members = ','.join(members_res)

    if 'status' in params:
        normalized_status = normalize_status(params['status'])
        if normalized_status:
            task.status = normalized_status

    if 'priority' in params:
        prio = str(params['priority']).lower()
        priority_map = {'גבוהה': 'high', 'בינונית': 'medium', 'נמוכה': 'low', 'ללא': 'none'}
        task.priority = priority_map.get(prio, prio)

    start_val = params.get('start_date') or params.get('new_start_date')
    if start_val is not None:
        task.start_date = parse_date_value(start_val)

    end_val = params.get('end_date') or params.get('new_end_date') or params.get('due_date') or params.get('target_date')
    if end_val is not None:
        task.end_date = parse_date_value(end_val)
    elif start_val is not None and params.get('status') == 'status-delayed':
        task.end_date = parse_date_value(start_val)

    if 'estimated_hours' in params:
        try:
            task.estimated_hours = float(params['estimated_hours']) if params['estimated_hours'] is not None else None
        except (ValueError, TypeError):
            pass

    if 'notes' in params:
        task.notes = params['notes']

    db.session.commit()
    return {
        'action': 'edit_task',
        'status': 'success',
        'task_id': task.id,
        'description': f'עודכנה משימה #{task.id}: "{task.task}"'
    }

def _action_delete_task(params):
    task = resolve_task(params)
    if not task:
        return {'action': 'delete_task', 'status': 'error', 'error': 'משימה למחיקה לא נמצאה'}

    task_id = task.id
    title = task.task
    db.session.delete(task)
    db.session.commit()
    return {
        'action': 'delete_task',
        'status': 'success',
        'description': f'נמחקה משימה #{task_id}: "{title}"'
    }

def _action_archive_task(params, is_archived=True):
    task = resolve_task(params)
    if not task:
        return {'action': 'archive_task', 'status': 'error', 'error': 'משימה לא נמצאה'}

    task.is_archived = is_archived
    if not is_archived:
        if task.project_id:
            proj = db.session.get(Project, task.project_id)
            if proj and proj.is_archived:
                proj.is_archived = False
        elif task.project:
            proj = Project.query.filter_by(name=task.project).first()
            if proj and proj.is_archived:
                proj.is_archived = False
    db.session.commit()
    action_text = 'הועברה לארכיון' if is_archived else 'שוחזרה מהארכיון'
    return {
        'action': 'archive_task' if is_archived else 'unarchive_task',
        'status': 'success',
        'task_id': task.id,
        'description': f'משימה #{task.id} "{task.task}" {action_text}'
    }

def _action_create_project(params):
    name = (params.get('name') or params.get('name_he') or params.get('project_name') or params.get('title') or '').strip()
    if not name:
        return {'action': 'create_project', 'status': 'error', 'error': 'שם פרויקט הוא שדה חובה'}

    existing = Project.query.filter_by(name=name).first()
    if existing:
        return {'action': 'create_project', 'status': 'error', 'error': f'פרויקט "{name}" כבר קיים'}

    team_ids = params.get('team_ids') or []
    teams_input = params.get('teams') or params.get('team') or params.get('team_names') or []
    if isinstance(teams_input, str):
        teams_input = [t.strip() for t in teams_input.split(',') if t.strip()]

    teams = []
    if team_ids:
        for tid in team_ids:
            try:
                t = db.session.get(Team, int(tid))
                if t and t not in teams:
                    teams.append(t)
            except (ValueError, TypeError):
                pass
    if teams_input:
        for t_name in teams_input:
            clean_t = str(t_name).strip()
            clean_t_no_prefix = re.sub(r'^צוות\s+', '', clean_t).strip()
            t_obj = Team.query.filter(
                (Team.name_he == clean_t) |
                (Team.name_he == clean_t_no_prefix) |
                (Team.name_en == clean_t.lower()) |
                (Team.name_en == clean_t_no_prefix.lower())
            ).first()
            if not t_obj:
                for t in Team.query.all():
                    if clean_t_no_prefix.lower() in t.name_he.lower() or clean_t_no_prefix.lower() in t.name_en.lower():
                        t_obj = t
                        break
            if t_obj and t_obj not in teams:
                teams.append(t_obj)

    if not teams:
        first_t = Team.query.first()
        if first_t:
            teams.append(first_t)

    project = Project(name=name, teams=teams)
    db.session.add(project)
    db.session.commit()

    teams_str = ', '.join([t.name_he for t in teams])
    return {
        'action': 'create_project',
        'status': 'success',
        'project_id': project.id,
        'description': f'נוצר פרויקט חדש: "{name}" (שויך לצוותים: {teams_str})'
    }

def _action_edit_project(params):
    proj_val = params.get('id') or params.get('project_id') or params.get('name') or params.get('old_name') or params.get('project') or params.get('project_name')
    project = resolve_project(proj_val)

    if not project:
        return {'action': 'edit_project', 'status': 'error', 'error': 'פרויקט לא נמצא'}

    new_name = (params.get('new_name') or '').strip()
    if not new_name and 'name' in params and proj_val and str(params.get('name')).strip() != project.name:
        new_name = str(params.get('name')).strip()

    if new_name and new_name != project.name:
        project.name = new_name
        for t in project.tasks:
            t.project = new_name

    # Handle teams: support team_ids, teams, team, team_name, add_team
    teams_input = []
    if 'team_name' in params or 'team' in params:
        raw_t = params.get('team_name') or params.get('team')
        teams_input = [raw_t] if isinstance(raw_t, str) else list(raw_t)
    elif 'teams' in params:
        raw_t = params.get('teams')
        teams_input = [raw_t] if isinstance(raw_t, str) else list(raw_t)

    teams_to_add = []
    for t_name in teams_input:
        clean_t = str(t_name).strip()
        clean_t_no_prefix = re.sub(r'^צוות\s+', '', clean_t).strip()
        t_obj = Team.query.filter(
            (Team.name_he == clean_t) |
            (Team.name_he == clean_t_no_prefix) |
            (Team.name_en == clean_t.lower()) |
            (Team.name_en == clean_t_no_prefix.lower())
        ).first()
        if not t_obj:
            for t in Team.query.all():
                if clean_t_no_prefix.lower() in t.name_he.lower() or clean_t_no_prefix.lower() in t.name_en.lower():
                    t_obj = t
                    break
        if t_obj and t_obj not in teams_to_add:
            teams_to_add.append(t_obj)

    if teams_to_add:
        is_add = params.get('add_team', True) or ('teams' not in params)
        if is_add:
            for t in teams_to_add:
                if t not in project.teams:
                    project.teams.append(t)
        else:
            project.teams = teams_to_add

    db.session.commit()
    teams_str = ', '.join([t.name_he for t in project.teams])
    return {
        'action': 'edit_project',
        'status': 'success',
        'description': f'עודכן פרויקט: "{project.name}" (צוותים: {teams_str})'
    }

def _action_delete_project(params):
    proj_val = params.get('id') or params.get('project_id') or params.get('name') or params.get('project_name') or params.get('project')
    project = resolve_project(proj_val)

    if not project:
        return {'action': 'delete_project', 'status': 'error', 'error': 'פרויקט למחיקה לא נמצא'}

    name = project.name
    # Delete all tasks belonging to this project
    Task.query.filter((Task.project_id == project.id) | (Task.project == project.name)).delete(synchronize_session='fetch')
    db.session.delete(project)
    db.session.commit()
    return {
        'action': 'delete_project',
        'status': 'success',
        'description': f'נמחק פרויקט: "{name}" וכל המשימות שבו'
    }

def _action_archive_project(params, is_archived=True):
    proj_val = params.get('id') or params.get('project_id') or params.get('name') or params.get('project_name') or params.get('project')
    project = resolve_project(proj_val)

    if not project:
        return {'action': 'archive_project', 'status': 'error', 'error': 'פרויקט לא נמצא'}

    project.is_archived = is_archived
    Task.query.filter((Task.project_id == project.id) | (Task.project == project.name)).update({'is_archived': is_archived}, synchronize_session='fetch')
    db.session.commit()
    action_text = 'הועבר לארכיון יחד עם כל משימותיו' if is_archived else 'שוחזר מהארכיון יחד עם כל משימותיו'
    return {
        'action': 'archive_project',
        'status': 'success',
        'description': f'פרויקט "{project.name}" {action_text}'
    }

def _action_create_team(params):
    name_en = params.get('name_en', '').strip().lower()
    name_he = params.get('name_he', '').strip()
    if not name_en or not name_he:
        return {'action': 'create_team', 'status': 'error', 'error': 'נדרש שם עברי ואנגלי לצוות'}

    existing = Team.query.filter((Team.name_en == name_en) | (Team.name_he == name_he)).first()
    if existing:
        return {'action': 'create_team', 'status': 'error', 'error': 'צוות בשם זה כבר קיים'}

    team = Team(name_en=name_en, name_he=name_he)
    db.session.add(team)
    db.session.commit()
    return {
        'action': 'create_team',
        'status': 'success',
        'team_id': team.id,
        'description': f'נוצר צוות חדש: "{name_he}" ({name_en})'
    }

def _action_edit_team(params):
    team_id = params.get('id') or params.get('team_id')
    team = db.session.get(Team, int(team_id)) if team_id else None
    if not team and params.get('name'):
        team = Team.query.filter((Team.name_he == params['name'].strip()) | (Team.name_en == params['name'].strip().lower())).first()

    if not team:
        return {'action': 'edit_team', 'status': 'error', 'error': 'צוות לא נמצא'}

    if 'name_he' in params: team.name_he = params['name_he'].strip()
    if 'name_en' in params: team.name_en = params['name_en'].strip().lower()

    db.session.commit()
    return {
        'action': 'edit_team',
        'status': 'success',
        'description': f'עודכן צוות: "{team.name_he}"'
    }

def _action_delete_team(params):
    team_id = params.get('id') or params.get('team_id')
    team = db.session.get(Team, int(team_id)) if team_id else None
    if not team:
        return {'action': 'delete_team', 'status': 'error', 'error': 'צוות למחיקה לא נמצא'}

    name = team.name_he
    db.session.delete(team)
    db.session.commit()
    return {
        'action': 'delete_team',
        'status': 'success',
        'description': f'נמחק צוות: "{name}"'
    }

def _action_create_member(params):
    name_he = params.get('name_he', '').strip()
    name_en = params.get('name_en', '').strip().lower()
    team_id = params.get('team_id')
    target_team = None

    if team_id:
        try:
            target_team = db.session.get(Team, int(team_id))
        except (ValueError, TypeError):
            target_team = None

    if not target_team and params.get('team'):
        t_clean = str(params['team']).strip()
        target_team = Team.query.filter((Team.name_he == t_clean) | (Team.name_en == t_clean.lower())).first()
        if not target_team:
            for t in Team.query.all():
                if t_clean in t.name_he or t.name_he in t_clean or t_clean.lower() in t.name_en.lower():
                    target_team = t
                    break

    if not target_team:
        target_team = Team.query.first()

    if target_team:
        team_id = target_team.id

    if not name_he or not name_en or not team_id:
        return {'action': 'create_member', 'status': 'error', 'error': 'נדרש שם עברי, שם אנגלי וצוות'}

    member = TeamMember(name_he=name_he, name_en=name_en, team_id=team_id)
    if target_team and target_team not in member.teams:
        member.teams.append(target_team)
    db.session.add(member)
    db.session.commit()
    return {
        'action': 'create_member',
        'status': 'success',
        'member_id': member.id,
        'description': f'נוסף חבר צוות חדש: "{name_he}" ({name_en})'
    }

def _action_delete_member(params):
    mem_id = params.get('id') or params.get('member_id')
    member = db.session.get(TeamMember, int(mem_id)) if mem_id else None
    if not member and params.get('name'):
        member = TeamMember.query.filter((TeamMember.name_he == params['name'].strip()) | (TeamMember.name_en == params['name'].strip().lower())).first()

    if not member:
        return {'action': 'delete_member', 'status': 'error', 'error': 'חבר צוות לא נמצא'}

    name = member.name_he
    db.session.delete(member)
    db.session.commit()
    return {
        'action': 'delete_member',
        'status': 'success',
        'description': f'נמחק חבר צוות: "{name}"'
    }

def _action_create_special_day(params):
    name = (params.get('name') or params.get('name_he') or params.get('title') or '').strip()
    d_val = parse_date_value(params.get('date'))
    if not name or not d_val:
        return {'action': 'create_special_day', 'status': 'error', 'error': 'נדרש שם ותאריך לחג/אירוע'}

    sd = SpecialDay(date=d_val, name=name, type=params.get('type', 'holiday'), color=params.get('color'))
    db.session.add(sd)
    db.session.commit()
    return {
        'action': 'create_special_day',
        'status': 'success',
        'special_day_id': sd.id,
        'description': f'נוסף יום מיוחד: "{name}" בתאריך {d_val.strftime("%d/%m/%Y")}'
    }

def _action_delete_special_day(params):
    sd_id = params.get('id')
    sd = db.session.get(SpecialDay, int(sd_id)) if sd_id else None
    if not sd:
        return {'action': 'delete_special_day', 'status': 'error', 'error': 'יום מיוחד לא נמצא'}

    name = sd.name
    db.session.delete(sd)
    db.session.commit()
    return {
        'action': 'delete_special_day',
        'status': 'success',
        'description': f'נמחק יום מיוחד: "{name}"'
    }
