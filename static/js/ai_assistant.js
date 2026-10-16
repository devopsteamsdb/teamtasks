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
            const editBtn = e.target.closest('.ai-task-edit-btn, .ai-task-pill');
            if (editBtn) {
                const taskId = editBtn.dataset.taskId;
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
 * Global helper to open the task edit popup modal for a specific task.
 * Works seamlessly whether called from the main dashboard, calendar, or AI assistant.
 */
window.openTaskEditModal = async function(taskId) {
    if (!taskId) return;
    const numId = parseInt(taskId, 10);
    if (isNaN(numId)) return;

    // 1. Direct DOM check (Main dashboard / task lists)
    const el = document.querySelector(`.task-item[data-id="${numId}"]`);
    if (el) {
        el.click();
        return;
    }

    // 2. Calendar view check
    if (window.calendarUI && window.calendarState) {
        let calTask = Array.isArray(window.calendarState.tasks)
            ? window.calendarState.tasks.find(t => t.id == numId)
            : null;
        if (calTask) {
            window.calendarUI.openTaskModal(calTask);
            return;
        }
        try {
            const res = await fetch(`/api/tasks/${numId}`);
            if (res.ok) {
                const task = await res.json();
                window.calendarUI.openTaskModal(task);
                return;
            }
        } catch (e) {
            console.error('Error opening calendar task modal:', e);
        }
    }

    // 3. Main dashboard fallback (e.g. task is filtered out or in archive view)
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

            if (window.mainUI && typeof window.mainUI.openEditModal === 'function') {
                window.mainUI.openEditModal(dummy);
            } else {
                taskModal.style.display = 'block';
            }
        } catch (e) {
            console.error('Failed to open task modal:', e);
        }
    }
};

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.teamtasksAI = new AIAssistant();
});
