/**
 * TeamTasks AI Assistant Client Script
 */

class AIAssistant {
    constructor() {
        this.history = [];
        this.isOpen = false;
        this.initElements();
        if (!this.panel || !this.fabBtn) return;
        this.bindEvents();
        this.fetchStatus();
        this.loadHistory();
        if (sessionStorage.getItem('teamtasks_ai_open') === 'true') {
            this.openPanel();
        }
    }

    initElements() {
        this.fabBtn = document.getElementById('aiFabBtn');
        this.panel = document.getElementById('aiPanel');
        this.closeBtn = document.getElementById('aiCloseBtn');
        this.clearBtn = document.getElementById('aiClearBtn');
        this.messagesContainer = document.getElementById('aiMessages');
        this.typingIndicator = document.getElementById('aiTypingIndicator');
        this.chatForm = document.getElementById('aiChatForm');
        this.inputText = document.getElementById('aiInputText');
        this.sendBtn = document.getElementById('aiSendBtn');
        this.providerBadge = document.getElementById('aiProviderBadge');
        this.providerName = document.getElementById('aiProviderName');
        this.statusBadge = document.getElementById('aiStatusBadge');
    }

    bindEvents() {
        this.fabBtn.addEventListener('click', () => this.togglePanel());
        this.closeBtn.addEventListener('click', () => this.closePanel());
        this.clearBtn.addEventListener('click', () => this.clearHistory());

        this.chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSend();
        });

        // Enter sends, Shift+Enter for newline
        this.inputText.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSend();
            }
        });

        // Auto-expand textarea
        this.inputText.addEventListener('input', () => {
            this.inputText.style.height = 'auto';
            this.inputText.style.height = Math.min(this.inputText.scrollHeight, 100) + 'px';
        });

        // Quick action chips
        document.querySelectorAll('.ai-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const action = chip.getAttribute('data-quick');
                const promptText = chip.getAttribute('data-text');
                if (action === 'prompt' && promptText) {
                    this.inputText.value = promptText + ' ';
                    this.inputText.focus();
                } else if (action) {
                    this.handleQuickAction(action, chip.innerText.trim());
                }
            });
        });

        // Delegated listener for task edit buttons and interactive pills
        this.messagesContainer.addEventListener('click', (e) => {
            const editBtn = e.target.closest('.ai-task-edit-btn, .ai-task-pill, [data-task-id]');
            if (editBtn) {
                const taskId = editBtn.dataset.taskId || editBtn.getAttribute('data-task-id');
                if (taskId) {
                    e.preventDefault();
                    e.stopPropagation();
                    window.openTaskEditModal(taskId);
                }
            }
        });
    }

    togglePanel() {
        this.isOpen ? this.closePanel() : this.openPanel();
    }

    openPanel() {
        this.isOpen = true;
        this.panel.classList.add('active');
        sessionStorage.setItem('teamtasks_ai_open', 'true');
        this.scrollToBottom();
        setTimeout(() => this.inputText.focus(), 150);
    }

    closePanel() {
        this.isOpen = false;
        this.panel.classList.remove('active');
        sessionStorage.removeItem('teamtasks_ai_open');
    }

    async fetchStatus() {
        try {
            const res = await fetch('/api/ai/status');
            const data = await res.json();
            if (data.success && data.status) {
                const st = data.status;
                if (st.configured) {
                    this.providerName.textContent = st.is_airgapped ? 'Airgap (Local)' : 'Cloudflare AI';
                    this.providerBadge.title = `מודל: ${st.model || 'Default'} (${st.name})`;
                    this.statusBadge.style.backgroundColor = '#10b981';
                } else {
                    this.providerName.textContent = 'לא מוגדר';
                    this.statusBadge.style.backgroundColor = '#ef4444';
                    this.providerBadge.title = st.hint || 'יש להגדיר משתני סביבה';
                }
            }
        } catch (err) {
            console.error('Error fetching AI status:', err);
            this.providerName.textContent = 'שגיאת חיבור';
            this.statusBadge.style.backgroundColor = '#f59e0b';
        }
    }

    loadHistory() {
        try {
            const saved = sessionStorage.getItem('teamtasks_ai_history');
            if (saved) {
                this.history = JSON.parse(saved);
                // Replay saved history in UI
                this.history.forEach(msg => {
                    this.renderMessage(msg.role, msg.content, msg.actions || [], false);
                });
            }
        } catch (e) {
            this.history = [];
        }
    }

    saveHistory() {
        try {
            // Keep last 15 messages in session storage
            const trimmed = this.history.slice(-15);
            sessionStorage.setItem('teamtasks_ai_history', JSON.stringify(trimmed));
        } catch (e) {}
    }

    clearHistory() {
        if (!confirm('האם ברצונך לנקות את היסטוריית השיחה הנוכחית?')) return;
        this.history = [];
        sessionStorage.removeItem('teamtasks_ai_history');
        
        // Remove all messages except the first welcome message and typing indicator
        const messages = this.messagesContainer.querySelectorAll('.ai-message');
        messages.forEach((msg, idx) => {
            if (idx > 0) msg.remove();
        });
    }

    async handleSend() {
        const text = this.inputText.value.trim();
        if (!text) return;

        // Reset input
        this.inputText.value = '';
        this.inputText.style.height = 'auto';

        // Add user message to UI
        this.renderMessage('user', text);
        this.history.push({ role: 'user', content: text });
        this.saveHistory();

        this.setLoading(true);

        try {
            const res = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    history: this.history
                })
            });

            const data = await res.json();
            if (data.success) {
                this.renderMessage('assistant', data.reply, data.actions);
                this.history.push({
                    role: 'assistant',
                    content: data.reply,
                    actions: data.actions
                });
                this.saveHistory();

                if (data.refresh_needed) {
                    this.handleDataRefresh();
                }
            } else {
                this.renderMessage('assistant', `⚠️ שגיאה: ${data.error || 'אירעה שגיאה בעיבוד הבקשה'}`);
            }
        } catch (err) {
            console.error('AI chat error:', err);
            this.renderMessage('assistant', '⚠️ שגיאת תקשורת עם שרת ה-AI. אנא נסה שוב.');
        } finally {
            this.setLoading(false);
        }
    }

    async handleQuickAction(actionType, actionLabel) {
        this.renderMessage('user', actionLabel);
        this.setLoading(true);

        try {
            const res = await fetch('/api/ai/quick', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: actionType })
            });

            const data = await res.json();
            if (data.success) {
                this.renderMessage('assistant', data.reply);
                this.history.push({ role: 'user', content: actionLabel });
                this.history.push({ role: 'assistant', content: data.reply });
                this.saveHistory();
            } else {
                this.renderMessage('assistant', `⚠️ שגיאה בביצוע פעולה: ${data.error || 'אירעה שגיאה'}`);
            }
        } catch (err) {
            console.error('AI quick action error:', err);
            this.renderMessage('assistant', '⚠️ שגיאת תקשורת עם שרת ה-AI.');
        } finally {
            this.setLoading(false);
        }
    }

    setLoading(loading) {
        if (loading) {
            this.typingIndicator.classList.add('active');
            this.sendBtn.disabled = true;
            this.scrollToBottom(true);
        } else {
            this.typingIndicator.classList.remove('active');
            this.sendBtn.disabled = false;
            this.scrollToBottom(true);
        }
    }

    renderMessage(role, content, actions = [], shouldScroll = true) {
        // Deduplicate content if actions cards already represent it
        if (actions && actions.length > 0 && content) {
            actions.forEach(act => {
                const desc = act.description || '';
                if (desc) {
                    content = content.split('\n').filter(line => {
                        const trimmed = line.trim();
                        return !(trimmed === desc || trimmed === `✅ ${desc}` || (trimmed.startsWith('✅') && trimmed.includes(desc)) || (trimmed.startsWith('-') && trimmed.includes(desc)));
                    }).join('\n').trim();
                }
            });
            // If only redundant success header remains, clear it
            if (content === 'בוצע בהצלחה:' || content === 'בוצע בהצלחה') {
                content = '';
            }
        }

        const msgDiv = document.createElement('div');
        msgDiv.className = `ai-message ${role}`;

        const bubble = document.createElement('div');
        bubble.className = 'ai-bubble';

        // Simple and robust markdown rendering
        bubble.innerHTML = this.formatMarkdown(content);

        // If actions were executed, render action summary cards
        if (actions && actions.length > 0) {
            actions.forEach(act => {
                const card = document.createElement('div');
                const isError = act.status === 'error';
                card.className = `ai-action-card ${isError ? 'error' : ''}`;

                const taskId = act.task_id || (act.task && act.task.id);
                let editBtnHtml = '';
                if (taskId && !isError) {
                    editBtnHtml = `
                        <button type="button" class="ai-task-edit-btn" data-task-id="${taskId}" title="ערוך משימה #${taskId}">
                            <i class="fas fa-edit"></i> ערוך משימה
                        </button>
                    `;
                }

                card.innerHTML = `
                    <div class="ai-action-main">
                        <span class="ai-action-icon">${isError ? '❌' : '✅'}</span>
                        <span class="ai-action-text">${this.escapeHtml(act.description || act.error || act.action)}</span>
                    </div>
                    ${editBtnHtml}
                `;
                bubble.appendChild(card);
            });
        }

        // If assistant response describes a single task, add a dedicated prominent edit button row
        if (role === 'assistant' && content) {
            const taskDetailMatch = content.match(/פרטי משימה #(\d+)/);
            if (taskDetailMatch) {
                const taskId = taskDetailMatch[1];
                const hasActionCard = actions && actions.some(a => (a.task_id == taskId || (a.task && a.task.id == taskId)));
                if (!hasActionCard) {
                    const actionRow = document.createElement('div');
                    actionRow.className = 'ai-task-actions-row';
                    actionRow.innerHTML = `
                        <button type="button" class="ai-task-edit-btn prominent" data-task-id="${taskId}" title="ערוך משימה #${taskId}">
                            <i class="fas fa-edit"></i> ערוך משימה #${taskId}
                        </button>
                    `;
                    bubble.appendChild(actionRow);
                }
            }
        }

        msgDiv.appendChild(bubble);

        // Insert before typing indicator
        this.messagesContainer.insertBefore(msgDiv, this.typingIndicator);

        if (shouldScroll) {
            this.scrollToBottom(true);
        }
    }

    formatMarkdown(text) {
        if (!text) return '';
        let escaped = this.escapeHtml(text);

        // Bold: **text**
        escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // Inline code: `code`
        escaped = escaped.replace(/`([^`]+)`/g, '<code>$1</code>');

        // Headers
        escaped = escaped.replace(/^### (.*$)/gim, '<h4 style="margin: 8px 0 4px; font-weight:700;">$1</h4>');
        escaped = escaped.replace(/^## (.*$)/gim, '<h3 style="margin: 10px 0 6px; font-weight:700;">$1</h3>');

        // Interactive task pills: replace `#(\d+)` with clickable task pill
        escaped = escaped.replace(/(^|[^\w&])#(\d+)\b/g, '$1<button type="button" class="ai-task-pill" data-task-id="$2" title="ערוך משימה #$2">#$2 <i class="fas fa-edit"></i></button>');
        // Also match Hebrew task mentions like "משימה 12" or "משימה מס' 12"
        escaped = escaped.replace(/(משימה\s+(?:מס'?\s+|מספר\s+)?)(?!<button)(\d+)\b/g, '$1<button type="button" class="ai-task-pill" data-task-id="$2" title="ערוך משימה #$2">#$2 <i class="fas fa-edit"></i></button>');

        // Line breaks & bullet/numbered lists
        const lines = escaped.split('\n');
        let listTag = null;
        let formatted = '';

        for (let line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith('* ') || trimmed.startsWith('- ') || trimmed.startsWith('• ')) {
                if (listTag !== 'ul') {
                    if (listTag) formatted += `</${listTag}>`;
                    formatted += '<ul style="margin: 4px 0 8px; padding-right: 20px;">';
                    listTag = 'ul';
                }
                formatted += `<li>${trimmed.substring(2)}</li>`;
            } else if (/^\d+\.\s/.test(trimmed)) {
                if (listTag !== 'ol') {
                    if (listTag) formatted += `</${listTag}>`;
                    formatted += '<ol style="margin: 4px 0 8px; padding-right: 20px;">';
                    listTag = 'ol';
                }
                const content = trimmed.replace(/^\d+\.\s/, '');
                formatted += `<li>${content}</li>`;
            } else {
                if (listTag) {
                    formatted += `</${listTag}>`;
                    listTag = null;
                }
                if (trimmed) {
                    formatted += `<p>${trimmed}</p>`;
                }
            }
        }
        if (listTag) formatted += `</${listTag}>`;

        return formatted;
    }

    escapeHtml(unsafe) {
        return (unsafe || '')
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    handleDataRefresh() {
        // Dispatch live event to update dashboard/calendar silently without any full page refresh
        window.dispatchEvent(new CustomEvent('teamtasks:refresh'));
        window.dispatchEvent(new CustomEvent('calendar:refresh'));

        if (typeof window.teamtasksNotifyChange === 'function') {
            window.teamtasksNotifyChange();
        } else if (typeof BroadcastChannel !== 'undefined') {
            try {
                new BroadcastChannel('teamtasks_live_sync').postMessage({ type: 'teamtasks:data_changed', timestamp: Date.now() });
            } catch (e) {}
        }

        if (typeof window.loadCalendarData === 'function') {
            window.loadCalendarData();
        }
    }

    scrollToBottom(smooth = true) {
        const container = this.messagesContainer;
        if (!container) return;

        if (this._scrollTimer) {
            clearTimeout(this._scrollTimer);
            this._scrollTimer = null;
        }

        const doScroll = (isSmooth) => {
            if (!container) return;
            const targetTop = container.scrollHeight;
            if (isSmooth) {
                container.scrollTo({
                    top: targetTop,
                    behavior: 'smooth'
                });
            } else {
                container.scrollTop = targetTop;
            }
        };

        // 1. Immediate scroll to new scrollHeight so view begins moving right away
        doScroll(false);

        // 2. Smooth scroll on next animation frame after layout is rendered
        requestAnimationFrame(() => {
            doScroll(smooth);
        });

        // 3. Safety snap after any CSS animation (fadeIn 0.25s) completes
        this._scrollTimer = setTimeout(() => {
            doScroll(false);
        }, 280);
    }
}

/**
 * Helper to format date ISO string (e.g. 2026-10-30) to dd/mm/yyyy for text inputs.
 */
function formatDateForInput(isoStr) {
    if (!isoStr) return '';
    try {
        const parts = isoStr.split('T')[0].split('-');
        if (parts.length === 3) {
            return `${parts[2]}/${parts[1]}/${parts[0]}`;
        }
    } catch (e) {}
    return isoStr;
}

/**
 * Helper to parse dd/mm/yyyy input string to ISO yyyy-mm-dd.
 */
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

/**
 * Helper to format comment timestamps.
 */
function formatCommentDate(dateStr) {
    if (!dateStr) return '';
    try {
        const d = new Date(dateStr);
        if (isNaN(d.getTime())) return dateStr;
        const day = String(d.getDate()).padStart(2, '0');
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const hours = String(d.getHours()).padStart(2, '0');
        const mins = String(d.getMinutes()).padStart(2, '0');
        return `${day}/${month} ${hours}:${mins}`;
    } catch {
        return dateStr;
    }
}

/**
 * Loads and renders subtasks checklist in standalone modal.
 */
async function loadStandaloneSubtasks(taskId) {
    const list = document.getElementById('subtasksList');
    const progText = document.getElementById('subtaskProgressText');
    const progBar = document.getElementById('subtaskProgressBar');
    if (!list) return;

    list.innerHTML = '<div style="color: var(--secondary); font-size: 0.8rem; padding: 4px;">טוען תתי-משימות...</div>';

    try {
        const res = await fetch(`/api/tasks/${taskId}/subtasks`);
        const subtasks = res.ok ? await res.json() : [];

        function renderSubtasks() {
            list.innerHTML = '';
            if (!subtasks || subtasks.length === 0) {
                list.innerHTML = '<div class="empty-subtasks-text">אין תתי-משימות. הוסף פריט צ\'ק-ליסט חדש למטה.</div>';
                if (progText) progText.textContent = '0/0';
                if (progBar) progBar.style.width = '0%';
                if (window.mainUI && typeof window.mainUI.updateTaskSubtaskBadges === 'function') {
                    window.mainUI.updateTaskSubtaskBadges(taskId, 0, 0);
                }
                if (window.teamtasksNotifyChange) {
                    window.teamtasksNotifyChange();
                }
                return;
            }
            const doneCount = subtasks.filter(s => s.is_completed).length;
            const pct = Math.round((doneCount / subtasks.length) * 100);
            if (progText) progText.textContent = `${doneCount}/${subtasks.length}`;
            if (progBar) progBar.style.width = `${pct}%`;

            if (window.mainUI && typeof window.mainUI.updateTaskSubtaskBadges === 'function') {
                window.mainUI.updateTaskSubtaskBadges(taskId, doneCount, subtasks.length);
            }
            if (window.teamtasksNotifyChange) {
                window.teamtasksNotifyChange();
            }

            subtasks.forEach(st => {
                const item = document.createElement('div');
                item.className = `subtask-item ${st.is_completed ? 'completed' : ''}`;
                
                const titleEscaped = (st.title || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                item.innerHTML = `
                    <input type="checkbox" class="subtask-checkbox" ${st.is_completed ? 'checked' : ''}>
                    <span class="subtask-title">${titleEscaped}</span>
                    <button type="button" class="subtask-delete-btn" title="מחק פריט">&times;</button>
                `;

                item.querySelector('.subtask-checkbox').addEventListener('change', async (e) => {
                    st.is_completed = e.target.checked;
                    try {
                        await fetch(`/api/subtasks/${st.id}`, {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ is_completed: st.is_completed })
                        });
                    } catch (err) {
                        console.error('Error toggling subtask:', err);
                    }
                    renderSubtasks();
                });

                item.querySelector('.subtask-delete-btn').addEventListener('click', async () => {
                    try {
                        await fetch(`/api/subtasks/${st.id}`, { method: 'DELETE' });
                        const idx = subtasks.findIndex(s => s.id === st.id);
                        if (idx !== -1) subtasks.splice(idx, 1);
                        renderSubtasks();
                    } catch (err) {
                        console.error('Error deleting subtask:', err);
                    }
                });

                list.appendChild(item);
            });
        }

        renderSubtasks();

        // Add subtask
        const addBtn = document.getElementById('addSubtaskBtn');
        const addInput = document.getElementById('newSubtaskInput');
        if (addBtn && addInput) {
            const doAdd = async () => {
                const title = addInput.value.trim();
                if (!title) return;
                addInput.value = '';
                try {
                    const createRes = await fetch(`/api/tasks/${taskId}/subtasks`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ title })
                    });
                    if (createRes.ok) {
                        const resData = await createRes.json();
                        const newSt = resData.subtask || resData;
                        subtasks.push(newSt);
                        renderSubtasks();
                    }
                } catch (err) {
                    console.error('Error adding subtask:', err);
                }
            };
            addBtn.onclick = doAdd;
            addInput.onkeydown = (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    doAdd();
                }
            };
        }
    } catch (e) {
        console.error('Error loading subtasks:', e);
    }
}

/**
 * Loads and renders comments in standalone modal.
 */
async function loadStandaloneComments(taskId, members = []) {
    const list = document.getElementById('commentsList');
    const counter = document.getElementById('commentCounter');
    const authorSelect = document.getElementById('commentAuthorSelect');
    if (!list) return;

    list.innerHTML = '<div style="color: var(--secondary); font-size: 0.8rem; padding: 4px;">טוען תגובות...</div>';

    if (authorSelect) {
        authorSelect.innerHTML = '<option value="">אנונימי / משתמש כללי</option>';
        members.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m.name;
            opt.textContent = m.name;
            opt.dataset.avatar = m.avatar || '';
            authorSelect.appendChild(opt);
        });
    }

    try {
        const res = await fetch(`/api/tasks/${taskId}/comments`);
        const comments = res.ok ? await res.json() : [];

        function renderComments() {
            list.innerHTML = '';
            if (counter) counter.textContent = comments.length;
            if (!comments || comments.length === 0) {
                list.innerHTML = '<div class="empty-comments-text">אין עדיין תגובות על משימה זו.</div>';
                return;
            }
            comments.forEach(c => {
                const item = document.createElement('div');
                item.className = 'comment-item';
                const authorEscaped = (c.author_name || 'אנונימי').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                const commentEscaped = (c.content || c.comment || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                const timeStr = c.created_at ? formatCommentDate(c.created_at) : '';

                item.innerHTML = `
                    <div class="comment-header">
                        ${c.author_avatar ? `<img src="${c.author_avatar}" class="comment-avatar" alt="${authorEscaped}">` : '<div class="comment-avatar-placeholder">👤</div>'}
                        <span class="comment-author-name">${authorEscaped}</span>
                        <span class="comment-timestamp">${timeStr}</span>
                        <button type="button" class="comment-delete-btn" title="מחק תגובה">&times;</button>
                    </div>
                    <div class="comment-text">${commentEscaped}</div>
                `;

                item.querySelector('.comment-delete-btn').addEventListener('click', async () => {
                    try {
                        await fetch(`/api/comments/${c.id}`, { method: 'DELETE' });
                        const idx = comments.findIndex(x => x.id === c.id);
                        if (idx !== -1) comments.splice(idx, 1);
                        renderComments();
                    } catch (err) {
                        console.error('Error deleting comment:', err);
                    }
                });

                list.appendChild(item);
            });
        }

        renderComments();

        // Add comment
        const addCommentBtn = document.getElementById('addCommentBtn');
        const newCommentInput = document.getElementById('newCommentInput');
        if (addCommentBtn && newCommentInput) {
            addCommentBtn.onclick = async () => {
                const commentText = newCommentInput.value.trim();
                if (!commentText) return;
                const authorName = authorSelect && authorSelect.value ? authorSelect.value : null;
                const authorAvatar = authorSelect && authorSelect.selectedOptions[0] ? (authorSelect.selectedOptions[0].dataset.avatar || null) : null;
                newCommentInput.value = '';

                try {
                    const postRes = await fetch(`/api/tasks/${taskId}/comments`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            content: commentText,
                            comment: commentText,
                            author_name: authorName,
                            author_avatar: authorAvatar
                        })
                    });

                    if (postRes.ok) {
                        const resData = await postRes.json();
                        const newC = resData.comment || resData;
                        comments.push(newC);
                        renderComments();
                    }
                } catch (err) {
                    console.error('Error adding comment:', err);
                }
            };
        }
    } catch (e) {
        console.error('Error loading comments:', e);
    }
}

/**
 * Opens task modal in standalone mode (e.g. from Admin page or without mainUI).
 */
window.openStandaloneTaskModal = async function(taskId) {
    const taskModal = document.getElementById('taskModal');
    if (!taskModal) {
        sessionStorage.setItem('teamtasks_ai_open', 'true');
        window.location.href = `/?open_task=${taskId}`;
        return;
    }

    try {
        const [taskRes, projectsRes, teamsRes, membersRes] = await Promise.all([
            fetch(`/api/tasks/${taskId}`),
            fetch('/api/projects'),
            fetch('/api/teams'),
            fetch('/api/members')
        ]);

        if (!taskRes.ok) {
            alert(`משימה #${taskId} לא נמצאה.`);
            return;
        }

        const task = await taskRes.json();
        const projects = projectsRes.ok ? await projectsRes.json() : [];
        const teams = teamsRes.ok ? await teamsRes.json() : [];
        const members = membersRes.ok ? await membersRes.json() : [];

        // Fill Title & Notes
        const nameInput = document.getElementById('taskNameInput');
        if (nameInput) nameInput.value = task.task || '';

        const notesInput = document.getElementById('taskNotes');
        if (notesInput) notesInput.value = task.notes || '';

        // Fill Status & Priority
        const statusSelect = document.getElementById('taskStatus');
        if (statusSelect) statusSelect.value = task.status || 'status-inprogress';

        const prioritySelect = document.getElementById('taskPriority');
        if (prioritySelect) prioritySelect.value = task.priority || 'none';

        // Fill Projects dropdown
        const projectSelect = document.getElementById('taskProject');
        if (projectSelect) {
            projectSelect.innerHTML = '<option value="">בחר פרויקט...</option>';
            projects.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.name;
                opt.textContent = p.name;
                if (p.name === task.project) opt.selected = true;
                projectSelect.appendChild(opt);
            });
            if (task.project && !projects.some(p => p.name === task.project)) {
                const opt = document.createElement('option');
                opt.value = task.project;
                opt.textContent = task.project;
                opt.selected = true;
                projectSelect.appendChild(opt);
            }
        }

        // Fill Teams dropdown
        const teamSelect = document.getElementById('taskTeam');
        if (teamSelect) {
            teamSelect.innerHTML = '<option value="">ללא צוות</option>';
            teams.forEach(t => {
                const opt = document.createElement('option');
                opt.value = t.id;
                opt.textContent = t.name;
                if (t.id == task.team_id) opt.selected = true;
                teamSelect.appendChild(opt);
            });
        }

        // Fill Dates with flatpickr support if available
        const startInput = document.getElementById('taskStartDate');
        const endInput = document.getElementById('taskEndDate');
        const startFormatted = formatDateForInput(task.start_date);
        const endFormatted = formatDateForInput(task.end_date);

        if (startInput) {
            startInput.value = startFormatted;
            if (typeof flatpickr !== 'undefined' && !startInput._flatpickr) {
                flatpickr(startInput, {
                    dateFormat: 'd/m/Y',
                    allowInput: true,
                    locale: typeof flatpickr.l10ns !== 'undefined' && flatpickr.l10ns.he ? flatpickr.l10ns.he : 'default'
                });
            } else if (startInput._flatpickr) {
                startInput._flatpickr.setDate(startFormatted, false);
            }
        }

        if (endInput) {
            endInput.value = endFormatted;
            if (typeof flatpickr !== 'undefined' && !endInput._flatpickr) {
                flatpickr(endInput, {
                    dateFormat: 'd/m/Y',
                    allowInput: true,
                    locale: typeof flatpickr.l10ns !== 'undefined' && flatpickr.l10ns.he ? flatpickr.l10ns.he : 'default'
                });
            } else if (endInput._flatpickr) {
                endInput._flatpickr.setDate(endFormatted, false);
            }
        }

        // Fill Members checkboxes
        const membersContainer = taskModal.querySelector('.members-select');
        if (membersContainer) {
            membersContainer.innerHTML = '';
            members.forEach(m => {
                const label = document.createElement('label');
                label.className = 'member-checkbox';
                const isChecked = Array.isArray(task.members) && task.members.includes(m.name);
                label.innerHTML = `
                    <input type="checkbox" value="${m.name}" data-img="${m.avatar || ''}" ${isChecked ? 'checked' : ''}>
                    ${m.avatar ? `<img src="${m.avatar}" class="avatar-small" alt="${m.name}">` : ''}
                    <span>${m.name}</span>
                `;
                membersContainer.appendChild(label);
            });
        }

        // Link to view in dashboard
        let openInDashBtn = taskModal.querySelector('.btn-open-in-dashboard');
        if (!openInDashBtn) {
            const headerTitleGroup = taskModal.querySelector('.modal-header-title-group');
            if (headerTitleGroup) {
                openInDashBtn = document.createElement('a');
                openInDashBtn.className = 'btn-open-in-dashboard';
                openInDashBtn.title = 'פתח משימה זו בלוח המשימות הראשי';
                openInDashBtn.innerHTML = `
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-left: 4px; vertical-align: middle;">
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                        <polyline points="15 3 21 3 21 9"></polyline>
                        <line x1="10" y1="14" x2="21" y2="3"></line>
                    </svg>פתח בלוח משימות
                `;
                openInDashBtn.style.cssText = 'display: inline-flex; align-items: center; margin-right: 12px; font-size: 0.8rem; color: #4f46e5; text-decoration: none; font-weight: 600; padding: 2px 8px; border-radius: 4px; background: rgba(79, 70, 229, 0.08);';
                headerTitleGroup.appendChild(openInDashBtn);
            }
        }
        if (openInDashBtn) {
            openInDashBtn.href = `/?open_task=${task.id}`;
        }

        // Subtasks & Comments
        loadStandaloneSubtasks(task.id);
        loadStandaloneComments(task.id, members);

        // Close handlers
        const closeBtn = taskModal.querySelector('.close-modal');
        if (closeBtn) {
            closeBtn.onclick = () => { taskModal.style.display = 'none'; };
        }
        taskModal.onclick = (e) => {
            if (e.target === taskModal) taskModal.style.display = 'none';
        };

        // Save button
        const saveBtn = document.getElementById('saveBtn');
        if (saveBtn) {
            saveBtn.onclick = async () => {
                saveBtn.disabled = true;
                const originalText = saveBtn.textContent;
                saveBtn.textContent = 'שומר...';

                try {
                    const selectedMembers = Array.from(taskModal.querySelectorAll('.members-select input[type="checkbox"]:checked'))
                        .map(cb => cb.value);

                    const payload = {
                        task: nameInput ? nameInput.value.trim() : task.task,
                        notes: notesInput ? notesInput.value.trim() : '',
                        status: statusSelect ? statusSelect.value : task.status,
                        priority: prioritySelect ? prioritySelect.value : task.priority,
                        project: projectSelect ? projectSelect.value : task.project,
                        team_id: teamSelect && teamSelect.value ? parseInt(teamSelect.value, 10) : null,
                        start_date: startInput ? parseDateInputToISO(startInput.value) : null,
                        end_date: endInput ? parseDateInputToISO(endInput.value) : null,
                        members: selectedMembers
                    };

                    const updateRes = await fetch(`/api/tasks/${task.id}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });

                    if (updateRes.ok) {
                        saveBtn.textContent = '✓ נשמר בהצלחה!';
                        setTimeout(() => {
                            saveBtn.disabled = false;
                            saveBtn.textContent = originalText;
                            taskModal.style.display = 'none';
                        }, 500);
                    } else {
                        const err = await updateRes.json();
                        alert('שגיאה בשמירה: ' + (err.error || 'שגיאה לא ידועה'));
                        saveBtn.disabled = false;
                        saveBtn.textContent = originalText;
                    }
                } catch (err) {
                    console.error('Error saving task:', err);
                    alert('שגיאת תקשורת בשמירת המשימה');
                    saveBtn.disabled = false;
                    saveBtn.textContent = originalText;
                }
            };
        }

        // Archive button
        const archiveBtn = document.getElementById('archiveBtn');
        if (archiveBtn) {
            archiveBtn.onclick = async () => {
                if (!confirm(`האם להעביר את משימה #${task.id} לארכיון?`)) return;
                try {
                    await fetch(`/api/tasks/${task.id}/archive`, { method: 'PUT' });
                    taskModal.style.display = 'none';
                } catch (err) {
                    console.error('Error archiving task:', err);
                }
            };
        }

        // Delete button
        const deleteBtn = document.getElementById('deleteBtn');
        if (deleteBtn) {
            deleteBtn.onclick = async () => {
                if (!confirm(`האם למחוק לצמיתות את משימה #${task.id}?`)) return;
                try {
                    await fetch(`/api/tasks/${task.id}`, { method: 'DELETE' });
                    taskModal.style.display = 'none';
                } catch (err) {
                    console.error('Error deleting task:', err);
                }
            };
        }

        // Display modal
        taskModal.style.display = 'block';

    } catch (e) {
        console.error('Failed to open standalone task modal:', e);
        sessionStorage.setItem('teamtasks_ai_open', 'true');
        window.location.href = `/?open_task=${taskId}`;
    }
};

/**
 * Global helper to open the task edit popup modal for a specific task.
 * Works seamlessly whether called from the main dashboard, admin page, or AI assistant.
 */
window.openTaskEditModal = async function(taskId) {
    if (!taskId) return;
    const numId = parseInt(taskId, 10);
    if (isNaN(numId)) return;

    // 1. Direct DOM check (Main dashboard / project cards)
    const el = document.querySelector(`.task-item[data-id="${numId}"]`);
    if (el) {
        el.click();
        return;
    }

    // 2. Main dashboard via mainUI fallback (e.g. task is in Kanban, Gantt, filtered out or in archive view)
    if (window.mainUI && typeof window.mainUI.openEditModal === 'function') {
        const taskModal = document.getElementById('taskModal');
        if (taskModal) {
            try {
                const res = await fetch(`/api/tasks/${numId}`);
                if (!res.ok) {
                    alert(`משימה #${numId} לא נמצאה.`);
                    return;
                }
                const task = await res.json();

                // Create a virtual task-item element to pass to UI.openEditModal
                const dummy = document.createElement('div');
                dummy.className = 'task-item';
                dummy.dataset.id = task.id;
                dummy.dataset.notes = task.notes || '';
                dummy.dataset.priority = task.priority || 'none';
                dummy.dataset.teamId = task.team_id || '';
                dummy.dataset.isArchived = task.is_archived ? 'true' : 'false';
                if (task.start_date) dummy.dataset.startDate = task.start_date;
                if (task.end_date) dummy.dataset.endDate = task.end_date;

                const nameSpan = document.createElement('span');
                nameSpan.className = 'task-name';
                nameSpan.textContent = task.task || '';
                dummy.appendChild(nameSpan);

                const statusSpan = document.createElement('span');
                statusSpan.className = `status-badge ${task.status || 'status-inprogress'}`;
                dummy.appendChild(statusSpan);

                if (Array.isArray(task.members)) {
                    task.members.forEach(m => {
                        const img = document.createElement('img');
                        img.className = 'avatar';
                        img.dataset.memberName = m;
                        dummy.appendChild(img);
                    });
                }

                const dummyProj = document.createElement('div');
                dummyProj.className = 'project-card';
                dummyProj.dataset.projectName = task.project || '';
                dummyProj.appendChild(dummy);

                if (typeof window.setCurrentTaskItem === 'function') {
                    window.setCurrentTaskItem(dummy);
                }

                window.mainUI.openEditModal(dummy);
                return;
            } catch (e) {
                console.error('Failed to open task modal via mainUI:', e);
            }
        }
    }

    // 3. Standalone mode (Admin page or any page without mainUI)
    const taskModal = document.getElementById('taskModal');
    if (taskModal && typeof window.openStandaloneTaskModal === 'function') {
        await window.openStandaloneTaskModal(numId);
        return;
    }

    // 4. Fallback: navigate to dashboard to open task
    sessionStorage.setItem('teamtasks_ai_open', 'true');
    window.location.href = `/?open_task=${numId}`;
};

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.teamtasksAI = new AIAssistant();
});
