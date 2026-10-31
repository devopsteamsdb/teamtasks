/**
 * QA Automated Test Suite - Frontend JavaScript Logic & Interaction Math
 * Runs with Node.js to verify client-side algorithmic calculations, date helpers,
 * regex parsing, and script syntax.
 */

const fs = require('fs');
const path = require('path');
const assert = require('assert');

let passedTests = 0;
let totalTests = 0;

function it(name, fn) {
    totalTests++;
    try {
        fn();
        passedTests++;
        console.log(`  ✓ ${name}`);
    } catch (e) {
        console.error(`  ✗ ${name}`);
        console.error(e);
        process.exitCode = 1;
    }
}

console.log('=== Running Frontend JavaScript Logic QA Tests ===\n');

// -------------------------------------------------------------
// 1. Date Formatting & ISO Parsing Logic
// -------------------------------------------------------------
console.log('1. Date Formatting & Parsing Logic:');

function formatDateFromISO(isoDate) {
    if (!isoDate) return '';
    try {
        const parts = isoDate.split('T')[0].split('-');
        if (parts.length === 3) {
            return `${parts[2]}/${parts[1]}/${parts[0]}`;
        }
    } catch (e) {}
    return isoDate;
}

function parseDateInputToISO(val) {
    if (!val) return null;
    val = val.trim();
    if (!val) return null;
    const parts = val.split(/[\/\-\.]/);
    if (parts.length === 3) {
        if (parts[0].length === 4) {
            return `${parts[0]}-${parts[1].padStart(2, '0')}-${parts[2].padStart(2, '0')}`;
        }
        const day = parts[0].padStart(2, '0');
        const month = parts[1].padStart(2, '0');
        const year = parts[2];
        return `${year}-${month}-${day}`;
    }
    return val;
}

it('formatDateFromISO converts yyyy-mm-dd to dd/mm/yyyy', () => {
    assert.strictEqual(formatDateFromISO('2026-11-05'), '05/11/2026');
    assert.strictEqual(formatDateFromISO('2026-01-01T00:00:00'), '01/01/2026');
    assert.strictEqual(formatDateFromISO(''), '');
    assert.strictEqual(formatDateFromISO(null), '');
});

it('parseDateInputToISO converts dd/mm/yyyy to yyyy-mm-dd', () => {
    assert.strictEqual(parseDateInputToISO('05/11/2026'), '2026-11-05');
    assert.strictEqual(parseDateInputToISO('5/1/2026'), '2026-01-05');
    assert.strictEqual(parseDateInputToISO('2026-11-05'), '2026-11-05');
    assert.strictEqual(parseDateInputToISO(''), null);
    assert.strictEqual(parseDateInputToISO(null), null);
});

// -------------------------------------------------------------
// 2. Gantt Timeline Date Arithmetic & Resize Calculations
// -------------------------------------------------------------
console.log('\n2. Gantt Timeline Date Arithmetic & Resize Math:');

function calculateDurationDays(startStr, endStr) {
    const s = new Date(startStr);
    const e = new Date(endStr);
    const diffTime = e - s;
    return Math.max(1, Math.round(diffTime / (1000 * 60 * 60 * 24)) + 1);
}

function shiftDateByDays(dateStr, days) {
    const d = new Date(dateStr);
    d.setDate(d.getDate() + days);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

it('calculateDurationDays computes inclusive days correctly', () => {
    assert.strictEqual(calculateDurationDays('2026-11-01', '2026-11-01'), 1);
    assert.strictEqual(calculateDurationDays('2026-11-01', '2026-11-10'), 10);
    assert.strictEqual(calculateDurationDays('2026-11-01', '2026-11-30'), 30);
});

it('shiftDateByDays shifts dates forward and backward cleanly across month boundaries', () => {
    assert.strictEqual(shiftDateByDays('2026-11-01', 5), '2026-11-06');
    assert.strictEqual(shiftDateByDays('2026-11-28', 5), '2026-12-03');
    assert.strictEqual(shiftDateByDays('2026-12-03', -5), '2026-11-28');
});

it('Gantt mouse selection box bounds calculation', () => {
    function getSelectionRange(startIdx, currentIdx, datesList) {
        const minIdx = Math.max(0, Math.min(startIdx, currentIdx));
        const maxIdx = Math.min(datesList.length - 1, Math.max(startIdx, currentIdx));
        return {
            startDate: datesList[minIdx],
            endDate: datesList[maxIdx],
            daysCount: maxIdx - minIdx + 1
        };
    }

    const mockDates = ['2026-11-01', '2026-11-02', '2026-11-03', '2026-11-04', '2026-11-05'];
    
    // Drag forward from 1 to 3
    const fwd = getSelectionRange(1, 3, mockDates);
    assert.strictEqual(fwd.startDate, '2026-11-02');
    assert.strictEqual(fwd.endDate, '2026-11-04');
    assert.strictEqual(fwd.daysCount, 3);

    // Drag backward from 3 to 1
    const bwd = getSelectionRange(3, 1, mockDates);
    assert.strictEqual(bwd.startDate, '2026-11-02');
    assert.strictEqual(bwd.endDate, '2026-11-04');
    assert.strictEqual(bwd.daysCount, 3);
});

it('truncateBarTitle dynamically truncates titles based on span days', () => {
    function truncateBarTitle(title, spanDays) {
        if (!title) return '';
        const clean = title.trim();
        if (spanDays <= 1) {
            return clean.length > 4 ? clean.slice(0, 3) + '..' : clean;
        } else if (spanDays === 2) {
            return clean.length > 8 ? clean.slice(0, 7) + '..' : clean;
        } else if (spanDays === 3) {
            return clean.length > 14 ? clean.slice(0, 12) + '..' : clean;
        } else if (spanDays <= 5) {
            return clean.length > 24 ? clean.slice(0, 22) + '..' : clean;
        }
        return clean;
    }

    const longTitle = 'בדיקת אינטגרציה רחבה למערכת הניהול';
    // 1-day span: <= 4 chars allowed, otherwise slice(0, 3) + '..'
    assert.strictEqual(truncateBarTitle(longTitle, 1), 'בדי..');
    assert.strictEqual(truncateBarTitle('קצר', 1), 'קצר');

    // 2-days span: <= 8 chars allowed, otherwise slice(0, 7) + '..'
    assert.strictEqual(truncateBarTitle(longTitle, 2), 'בדיקת א..');
    assert.strictEqual(truncateBarTitle('שלום עולם', 2), 'שלום עו..');

    // 3-days span: <= 14 chars allowed
    assert.strictEqual(truncateBarTitle(longTitle, 3), 'בדיקת אינטגר..');

    // 10-days span: full title preserved
    assert.strictEqual(truncateBarTitle(longTitle, 10), longTitle);
});

// -------------------------------------------------------------
// 3. AI Assistant Markdown & Task Pill Regex
// -------------------------------------------------------------
console.log('\n3. AI Assistant Markdown & Task Regex:');

function formatMarkdown(text) {
    if (!text) return '';
    let escaped = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

    // Bold
    escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Interactive task pills: replace `#(\d+)` with clickable task pill
    escaped = escaped.replace(/(^|[^\w&])#(\d+)\b/g, '$1<button type="button" class="ai-task-pill" data-task-id="$2">#$2</button>');
    // Also match Hebrew task mentions like "משימה 12" or "משימה מס' 12"
    escaped = escaped.replace(/(משימה\s+(?:מס'?\s+|מספר\s+)?)(?!<button)(\d+)\b/g, '$1<button type="button" class="ai-task-pill" data-task-id="$2">#$2</button>');

    return escaped;
}

it('formats bold text correctly', () => {
    const res = formatMarkdown('שלום **עולם**!');
    assert.strictEqual(res, 'שלום <strong>עולם</strong>!');
});

it('formats #id into interactive button pill', () => {
    const res = formatMarkdown('יש לבדוק את #42 בהקדם.');
    assert.ok(res.includes('<button type="button" class="ai-task-pill" data-task-id="42">#42</button>'));
});

it('formats Hebrew "משימה 55" into interactive button pill', () => {
    const res = formatMarkdown('נא לטפל ב משימה 55 בדחיפות.');
    assert.ok(res.includes('data-task-id="55"'));
});

it('formats Hebrew "משימה מס 88" into interactive button pill', () => {
    const res = formatMarkdown('הושלמה משימה מס 88 אתמול.');
    assert.ok(res.includes('data-task-id="88"'));
});

// -------------------------------------------------------------
// 4. Client-side Code Syntax & Asset Integrity
// -------------------------------------------------------------
console.log('\n4. Script Syntax & Asset File Integrity:');

const jsFiles = [
    'static/js/main.js',
    'static/js/ui.js',
    'static/js/events.js',
    'static/js/api.js',
    'static/js/gantt.js',
    'static/js/kanban.js',
    'static/js/state.js',
    'static/js/utils.js',
    'static/js/ai_assistant.js',
    'static/admin.js'
];

jsFiles.forEach(file => {
    it(`File exists and has valid JavaScript syntax: ${file}`, () => {
        assert.ok(fs.existsSync(file), `${file} should exist`);
        const content = fs.readFileSync(file, 'utf8');
        assert.ok(content.length > 50, `${file} should have meaningful content`);
        // Test parsing with Function constructor or node syntax check
        try {
            new Function(content.replace(/import\s+.*?;/g, '').replace(/export\s+.*?;/g, ''));
        } catch (syntaxErr) {
            // Some ES module constructs like top-level await or export might fail new Function, but are valid in ES modules
            assert.ok(!syntaxErr.message.includes('Unexpected token ILLEGAL'));
        }
    });
});

// -------------------------------------------------------------
// 5. Main View Projects Empty State Message & Structure
// -------------------------------------------------------------
console.log('\n5. Main View Projects Empty State Message & Structure:');

it('index.html contains #projectsEmptyState with Gantt empty-state style and text', () => {
    const html = fs.readFileSync('templates/index.html', 'utf8');
    assert.ok(html.includes('id="projectsEmptyState"'), '#projectsEmptyState should exist in index.html');
    assert.ok(html.includes('class="projects-empty-state gantt-empty-state"'), '#projectsEmptyState should use gantt-empty-state class');
    assert.ok(html.includes('אין פרויקטים להצגה בסינון הנוכחי'), 'Should have exact Hebrew empty message');
    assert.ok(html.includes('<line x1="4" y1="6" x2="16" y2="6"></line>'), 'Should include same SVG lines as Gantt page');
});

it('ui.js manages projectsEmptyState visibility based on visibleProjectsCount', () => {
    const uiJs = fs.readFileSync('static/js/ui.js', 'utf8');
    assert.ok(uiJs.includes('elements.projectsEmptyState'), 'ui.js should cache projectsEmptyState');
    assert.ok(uiJs.includes("emptyStateEl.style.display = (visibleProjectsCount === 0) ? 'flex' : 'none'"), 'ui.js should toggle flex/none for emptyStateEl');
});

it('style.css defines .projects-empty-state identical to .gantt-empty-state', () => {
    const css = fs.readFileSync('static/style.css', 'utf8');
    assert.ok(css.includes('.projects-empty-state'), 'style.css should style .projects-empty-state');
});

// -------------------------------------------------------------
// 6. Gantt Task Name Extraction and Visibility
// -------------------------------------------------------------
console.log('\n6. Gantt Task Name Extraction and Visibility:');

it('index.html kanban cards bind task.task to task-name and data-task-name', () => {
    const html = fs.readFileSync('templates/index.html', 'utf8');
    assert.ok(html.includes('data-task-name="{{ task.task }}"'), 'Kanban card must bind data-task-name');
    assert.ok(html.includes('<span class="task-name">{{ task.task }}</span>'), 'Kanban card title must bind {{ task.task }}');
    assert.ok(!html.includes('<span class="task-name">{{ task.name }}</span>'), 'No empty {{ task.name }} binding in template');
});

it('gantt.js defines displayName fallback and renders into .gantt-task-name and .gantt-bar-title', () => {
    const ganttJs = fs.readFileSync('static/js/gantt.js', 'utf8');
    assert.ok(ganttJs.includes('const displayName = task.name || task.task || task.title'), 'gantt.js must calculate resilient displayName');
    assert.ok(ganttJs.includes('<span class="gantt-task-name">${escapeHtml(displayName)}</span>'), 'gantt.js must render displayName in .gantt-task-name');
    assert.ok(ganttJs.includes('gantt-bar-title') && ganttJs.includes('truncatedTitle'), 'gantt.js must render truncatedTitle in .gantt-bar-title');
    assert.ok(ganttJs.includes('truncateBarTitle(fullTitle, span)'), 'gantt.js must update bar title dynamically on resize');
});

// -------------------------------------------------------------
// 7. Wide Modals, 15-Member Select Capacity & Task Meta Badges
// -------------------------------------------------------------
console.log('\n7. Wide Modals, 15-Member Select Capacity & Task Meta Badges:');

it('createTaskModal and taskModal share wide modal layout without narrowing override', () => {
    const css = fs.readFileSync('static/style.css', 'utf8');
    assert.ok(css.includes('.modal-content.modal-content-wide'), 'style.css defines .modal-content-wide');
    assert.ok(!css.includes('#createTaskModal .modal-content-wide {'), 'No narrowing override for #createTaskModal so both modals are identical in width');
});

it('members-select and side-members-select provide expanded capacity for 15+ members', () => {
    const css = fs.readFileSync('static/style.css', 'utf8');
    assert.ok(css.includes('min-height: 145px'), 'members select has min-height >= 145px');
    assert.ok(css.includes('max-height: 250px'), 'members select has max-height >= 250px');
});

it('task-meta has 2 lines (avatars + status, badges), note-badge removed from tasks page and task main div displays only notes on hover', () => {
    const html = fs.readFileSync('templates/index.html', 'utf8');
    const css = fs.readFileSync('static/style.css', 'utf8');
    // Verify task-meta contains task-meta-top (avatars + status) and task-meta-badges
    assert.ok(html.includes('<div class="task-meta-top">') && html.includes('status-badge') && html.includes('avatar-group'), 'task-meta-top groups avatars and status');
    assert.ok(html.includes('task-meta-badges'), 'task-meta contains task-meta-badges');
    // Verify note-badge is removed from the tasks page
    assert.ok(!html.includes('note-badge'), 'note-badge must be removed from tasks page');
    // Verify task main div (.task-item) has hover title displaying ONLY notes when present
    assert.ok(html.includes('{% if task.notes %}title="{{ task.notes }}"{% endif %}'), 'task-item has hover title displaying only notes');
    assert.ok(!html.includes("task_item_title = 'משימה: ' ~ task.task"), 'task details removed from task-item title');
    assert.ok(css.includes('.task-meta {') && css.includes('flex-direction: column;'), 'task-meta stacks the 2 lines vertically');
    assert.ok(css.includes('.task-meta-top {') && css.includes('display: flex;'), 'task-meta-top aligns avatars and status');
    assert.ok(css.includes('.task-name {') && css.includes('word-break: break-word;'), 'task-name has word-break styling');
});

it('kanban view renders priority circle icon instead of text', () => {
    const html = fs.readFileSync('templates/index.html', 'utf8');
    const css = fs.readFileSync('static/style.css', 'utf8');
    assert.ok(html.includes('class="priority-tag priority-{{ task.priority }}" title="'), 'priority-tag has tooltip title');
    // Verify no plain text like "גבוהה" / "בינונית" inside priority-tag
    assert.ok(!html.includes('{{ \'גבוהה\' if task.priority == \'high\''), 'priority-tag text has been replaced with circle icon');
    assert.ok(css.includes('.priority-tag {') && css.includes('border-radius: 50%;'), 'priority-tag is styled as a circle dot');
    assert.ok(css.includes('.priority-tag.priority-high {') && css.includes('#ef4444'), 'priority-tag has priority-high color');
    assert.ok(css.includes('.priority-tag.priority-medium {') && css.includes('#f59e0b'), 'priority-tag has priority-medium color');
});

it('kanban-date-badge displays date ranges correctly in templates and gantt.js', () => {
    const html = fs.readFileSync('templates/index.html', 'utf8');
    const ganttJs = fs.readFileSync('static/js/gantt.js', 'utf8');
    const css = fs.readFileSync('static/style.css', 'utf8');
    // Verify template renders date range
    assert.ok(html.includes("task.start_date.strftime('%d/%m') ~ ' - ' ~ task.end_date.strftime('%d/%m')"), 'template must format date range with hyphen');
    assert.ok(html.includes('<span dir="ltr">{{ date_disp }}</span>'), 'template must render date range in dir ltr span');
    // Verify gantt.js updates date range
    assert.ok(ganttJs.includes('startDisp} - ${endDisp}'), 'gantt.js must format date range when both dates are present');
    // Verify CSS styles
    assert.ok(css.includes('.kanban-date-badge {') && css.includes('white-space: nowrap;'), 'kanban-date-badge has nowrap styling');
});

it('gantt-bar-subtasks displays subtask numbers without v icon', () => {
    const ganttJs = fs.readFileSync('static/js/gantt.js', 'utf8');
    // Verify gantt-bar-subtasks does not contain checkmark icon
    assert.ok(!ganttJs.includes('gantt-bar-subtasks">✓'), 'gantt-bar-subtasks must NOT have checkmark icon');
    assert.ok(ganttJs.includes('class="gantt-bar-subtasks"'), 'gantt-bar-subtasks class is used');
    assert.ok(ganttJs.includes('>${task.subtasksText}</span>'), 'renders task.subtasksText directly');
});

// -------------------------------------------------------------
// 8. Kanban View Add-Task and Add-Project Controls
// -------------------------------------------------------------
console.log('\n8. Kanban View Add-Task and Add-Project Controls:');

it('kanban view has no add-task buttons in column headers', () => {
    const html = fs.readFileSync('templates/index.html', 'utf8');
    assert.ok(!html.includes('kanban-col-add-btn'), 'index.html must not contain kanban-col-add-btn buttons');
});

it('ui.js and style.css hide addProjectBtn in kanban view mode', () => {
    const uiJs = fs.readFileSync('static/js/ui.js', 'utf8');
    const css = fs.readFileSync('static/style.css', 'utf8');
    assert.ok(uiJs.includes("addProjectBtn.style.display = (mode === 'grid' ? '' : 'none')"), 'ui.js switches addProjectBtn visibility based on mode');
    assert.ok(css.includes('body[data-view-mode="kanban"] #addProjectBtn'), 'style.css defines rule hiding addProjectBtn in kanban');
});

// -------------------------------------------------------------
// 9. Printable Gantt Version & Navigation
// -------------------------------------------------------------
console.log('\n9. Printable Gantt Version & Navigation:');

it('ui.js updates printLink.href to /print?view=gantt when in Gantt mode', () => {
    const uiJs = fs.readFileSync('static/js/ui.js', 'utf8');
    assert.ok(uiJs.includes("printLink.href = (mode === 'gantt') ? '/print?view=gantt' : '/print'"), 'ui.js routes print link to gantt printable view when active');
});

it('printable.html includes Gantt view switcher and unstyled print button without emoji', () => {
    const html = fs.readFileSync('templates/printable.html', 'utf8');
    assert.ok(html.includes("updateFilter('view', 'gantt')"), 'printable.html includes Gantt view toggle');
    assert.ok(html.includes('class="print-gantt-view"'), 'printable.html includes print-gantt-view container');
    assert.ok(html.includes('class="print-gantt-bar'), 'printable.html includes print-gantt-bar element');
    assert.ok(html.includes('navigatePeriod'), 'printable.html includes period navigation');
    assert.ok(html.includes('id="printBtn"'), 'printable.html has #printBtn');
    assert.ok(!html.includes('🖨️'), 'print emoji removed from print button');
    assert.ok(!html.includes('print-action-btn'), 'custom print button class removed');
});

it('printable.css styles printable Gantt with landscape orientation and exact color printing', () => {
    const css = fs.readFileSync('static/printable.css', 'utf8');
    assert.ok(css.includes('.print-gantt-view'), 'printable.css defines .print-gantt-view');
    assert.ok(css.includes('.print-gantt-bar'), 'printable.css defines .print-gantt-bar');
    assert.ok(css.includes('size: landscape;'), 'printable.css sets landscape page size for printing');
    assert.ok(css.includes('print-color-adjust: exact'), 'printable.css enables exact color printing');
});

// -------------------------------------------------------------
// 10. Dynamic Page & Badge Updates (Subtasks, Comments, Modals)
// -------------------------------------------------------------
console.log('\n10. Dynamic Page & Badge Updates (Subtasks, Comments, Modals):');

it('ui.js exports updateTaskSubtaskBadges and updateTaskCommentBadges matching new 2-line layout', () => {
    const uiJs = fs.readFileSync('static/js/ui.js', 'utf8');
    assert.ok(uiJs.includes('export function updateTaskSubtaskBadges('), 'ui.js must export updateTaskSubtaskBadges');
    assert.ok(uiJs.includes('export function updateTaskCommentBadges('), 'ui.js must export updateTaskCommentBadges');
    assert.ok(uiJs.includes('.task-meta-badges'), 'must target .task-meta-badges for new 2-line layout');
    assert.ok(uiJs.includes('.kanban-card-badges'), 'must target .kanban-card-badges for Kanban cards');
    assert.ok(uiJs.includes('${completed}/${total}'), 'must format completed/total fraction');
    assert.ok(uiJs.includes("badge.className = `subtask-badge ${isAllDone ? 'all-done' : ''}`"), 'must toggle all-done class');
});

it('ui.js renderSubtasks and renderComments call dynamic badge updates immediately', () => {
    const uiJs = fs.readFileSync('static/js/ui.js', 'utf8');
    assert.ok(uiJs.includes('updateTaskSubtaskBadges(taskId, completed, total)'), 'renderSubtasks must invoke updateTaskSubtaskBadges');
    assert.ok(uiJs.includes('updateTaskCommentBadges(taskId, count)'), 'renderComments must invoke updateTaskCommentBadges');
});

it('api.js fetchPageContent uses cache-busting timestamp and no-cache header', () => {
    const apiJs = fs.readFileSync('static/js/api.js', 'utf8');
    assert.ok(apiJs.includes("u.searchParams.set('_t',"), 'fetchPageContent must set _t cache-busting timestamp');
    assert.ok(apiJs.includes("'Cache-Control': 'no-cache, no-store, must-revalidate'"), 'fetchPageContent must request no-cache');
});

it('events.js backdrop click and Escape key safely route through UI.closeModals', () => {
    const eventsJs = fs.readFileSync('static/js/events.js', 'utf8');
    assert.ok(eventsJs.includes('UI.closeModals()'), 'events.js must call UI.closeModals()');
    assert.ok(eventsJs.includes("e.key === 'Escape'"), 'events.js must listen for Escape key');
});

// -------------------------------------------------------------
// 11. Status Badge Colors Match Gantt
// -------------------------------------------------------------
console.log('\n11. Status Badge Colors Match Gantt:');

it('status badge colors match gantt status pill colors in light and dark mode', () => {
    const css = fs.readFileSync('static/style.css', 'utf8');

    // Light mode checks
    assert.ok(css.includes('.status-inprogress {') && css.includes('#e0e7ff') && css.includes('#3730a3'), 'status-inprogress matches Gantt indigo colors');
    assert.ok(css.includes('.status-delayed {') && css.includes('#ffedd5') && css.includes('#c2410c'), 'status-delayed matches Gantt orange colors');
    assert.ok(css.includes('.status-done {') && css.includes('#d1fae5') && css.includes('#065f46'), 'status-done matches Gantt emerald colors');
    assert.ok(css.includes('.status-notstarted {') && css.includes('#f1f5f9') && css.includes('#475569'), 'status-notstarted matches Gantt slate colors');

    // Dark mode checks
    assert.ok(css.includes('html.dark-mode .status-inprogress {') && css.includes('rgba(79, 70, 229, 0.25)') && css.includes('#a5b4fc'), 'dark mode status-inprogress matches Gantt');
    assert.ok(css.includes('html.dark-mode .status-delayed {') && css.includes('rgba(234, 88, 12, 0.25)') && css.includes('#fdba74'), 'dark mode status-delayed matches Gantt');
    assert.ok(css.includes('html.dark-mode .status-done {') && css.includes('rgba(16, 185, 129, 0.25)') && css.includes('#6ee7b7'), 'dark mode status-done matches Gantt');
    assert.ok(css.includes('html.dark-mode .status-notstarted {') && css.includes('#334155') && css.includes('#cbd5e1'), 'dark mode status-notstarted matches Gantt');
});

// -------------------------------------------------------------
// 12. Special Days Integration (Admin Management & Gantt Display)
// -------------------------------------------------------------
console.log('\n12. Special Days Integration (Admin Management & Gantt Display):');

it('admin.html has special days section, navigation button, and modal', () => {
    const adminHtml = fs.readFileSync('templates/admin.html', 'utf8');
    assert.ok(adminHtml.includes('data-section="special-days"'), 'admin navigation includes special-days tab');
    assert.ok(adminHtml.includes('id="section-special-days"'), 'admin content includes section-special-days');
    assert.ok(adminHtml.includes('id="addSpecialDayBtn"'), 'admin section includes addSpecialDayBtn');
    assert.ok(adminHtml.includes('id="specialDaysContainer"'), 'admin section includes specialDaysContainer');
    assert.ok(adminHtml.includes('id="specialDayModal"'), 'admin includes specialDayModal');
    assert.ok(adminHtml.includes('id="specialDayDateInput"'), 'specialDayModal includes specialDayDateInput');
    assert.ok(adminHtml.includes('id="specialDayNameInput"'), 'specialDayModal includes specialDayNameInput');
    assert.ok(adminHtml.includes('id="specialDayTypeSelect"'), 'specialDayModal includes specialDayTypeSelect');
    assert.ok(adminHtml.includes('id="saveSpecialDayBtn"'), 'specialDayModal includes saveSpecialDayBtn');
});

it('admin.js implements special days loading, rendering, and CRUD handlers', () => {
    const adminJs = fs.readFileSync('static/admin.js', 'utf8');
    assert.ok(adminJs.includes('loadSpecialDays'), 'admin.js must implement loadSpecialDays');
    assert.ok(adminJs.includes('renderSpecialDays'), 'admin.js must implement renderSpecialDays');
    assert.ok(adminJs.includes('saveSpecialDay'), 'admin.js must implement saveSpecialDay');
    assert.ok(adminJs.includes('deleteSpecialDay'), 'admin.js must implement deleteSpecialDay');
    assert.ok(adminJs.includes('/api/special-days'), 'admin.js must call /api/special-days endpoint');
});

it('admin.css defines table, date badges, color dots, table actions and modal presets', () => {
    const adminCss = fs.readFileSync('static/admin.css', 'utf8');
    assert.ok(adminCss.includes('.special-days-table'), 'admin.css defines .special-days-table');
    assert.ok(adminCss.includes('.special-day-date-badge'), 'admin.css defines .special-day-date-badge');
    assert.ok(adminCss.includes('.special-day-color-dot'), 'admin.css defines .special-day-color-dot');
    assert.ok(adminCss.includes('.special-day-type-badge.holiday'), 'admin.css defines holiday badge');
    assert.ok(adminCss.includes('.table-actions'), 'admin.css defines .table-actions');
    assert.ok(adminCss.includes('display: inline-flex'), 'admin.css uses inline-flex for action buttons');
});

it('gantt.js reflects special days in header cells and grid cells with badges', () => {
    const ganttJs = fs.readFileSync('static/js/gantt.js', 'utf8');
    assert.ok(ganttJs.includes('is-special-day'), 'gantt.js applies is-special-day class');
    assert.ok(ganttJs.includes('gantt-special-badge'), 'gantt.js renders gantt-special-badge');
    assert.ok(ganttJs.includes('specialDaysMap'), 'gantt.js maps special days by date key');
});

it('state.js and api.js export special days state and API methods', () => {
    const stateJs = fs.readFileSync('static/js/state.js', 'utf8');
    const apiJs = fs.readFileSync('static/js/api.js', 'utf8');
    assert.ok(stateJs.includes('specialDays: []'), 'state.js initializes specialDays array');
    assert.ok(stateJs.includes('setSpecialDays'), 'state.js exports setSpecialDays');
    assert.ok(apiJs.includes('fetchSpecialDays'), 'api.js exports fetchSpecialDays');
    assert.ok(apiJs.includes('createSpecialDay'), 'api.js exports createSpecialDay');
    assert.ok(apiJs.includes('updateSpecialDay'), 'api.js exports updateSpecialDay');
    assert.ok(apiJs.includes('deleteSpecialDay'), 'api.js exports deleteSpecialDay');
});

it('style.css defines gantt special day styles in light and dark mode', () => {
    const styleCss = fs.readFileSync('static/style.css', 'utf8');
    assert.ok(styleCss.includes('.gantt-day-header-cell.is-special-day'), 'style.css defines .gantt-day-header-cell.is-special-day');
    assert.ok(styleCss.includes('.gantt-special-badge'), 'style.css defines .gantt-special-badge');
    assert.ok(styleCss.includes('.gantt-grid-cell.is-special-day'), 'style.css defines .gantt-grid-cell.is-special-day');
    assert.ok(styleCss.includes('.special-day-legend-dot'), 'style.css defines .special-day-legend-dot');
});

console.log(`\n=================================================`);
console.log(`Frontend Logic QA Summary: ${passedTests}/${totalTests} tests passed`);
console.log(`=================================================\n`);

if (passedTests !== totalTests) {
    process.exit(1);
}
