// Kanban Module
import * as API from './api.js';
import { notifyDataChanged } from './live_sync.js';

export function updateKanbanCounters() {
    const columns = document.querySelectorAll('.kanban-column');
    columns.forEach(col => {
        const status = col.dataset.status;
        const countBadge = col.querySelector('.kanban-col-count') || document.getElementById(`count-${status}`);
        if (!countBadge) return;

        const cards = col.querySelectorAll('.kanban-card');
        let visibleCount = 0;
        cards.forEach(card => {
            if (!card.classList.contains('filtered-hidden') && !card.classList.contains('search-hidden')) {
                visibleCount++;
            }
        });

        countBadge.textContent = visibleCount;
    });
}

export function initKanbanDragAndDrop() {
    const cards = document.querySelectorAll('.kanban-card');
    const columns = document.querySelectorAll('.kanban-column');

    cards.forEach(card => {
        card.setAttribute('draggable', 'true');

        card.ondragstart = (e) => {
            e.dataTransfer.setData('text/plain', card.dataset.id);
            e.dataTransfer.effectAllowed = 'move';
            card.classList.add('dragging');
        };

        card.ondragend = () => {
            card.classList.remove('dragging');
            columns.forEach(c => c.classList.remove('drag-over'));
        };
    });

    columns.forEach(col => {
        col.ondragover = (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            col.classList.add('drag-over');
        };

        col.ondragleave = (e) => {
            // Only remove if leaving the column boundary
            if (!col.contains(e.relatedTarget)) {
                col.classList.remove('drag-over');
            }
        };

        col.ondrop = async (e) => {
            e.preventDefault();
            col.classList.remove('drag-over');

            const taskId = e.dataTransfer.getData('text/plain');
            if (!taskId) return;

            const targetStatus = col.dataset.status;
            const card = document.querySelector(`.kanban-card[data-id="${taskId}"]`);
            if (!card) return;

            const oldStatus = card.dataset.status;
            if (oldStatus === targetStatus) return;

            // Immediate DOM move for instantaneous UI response
            const body = col.querySelector('.kanban-column-body');
            if (body) {
                body.appendChild(card);
            }
            card.dataset.status = targetStatus;

            // Update matching card in Projects Grid if present
            const gridItem = document.querySelector(`.projects-grid .task-item[data-id="${taskId}"]`);
            if (gridItem) {
                gridItem.dataset.status = targetStatus;
                const statusBadge = gridItem.querySelector('.status-badge');
                if (statusBadge) {
                    statusBadge.className = `status-badge ${targetStatus}`;
                    const labels = {
                        'status-notstarted': 'טרם החל',
                        'status-inprogress': 'בתהליך',
                        'status-delayed': 'מעוכב',
                        'status-done': 'הושלם'
                    };
                    statusBadge.textContent = labels[targetStatus] || targetStatus;
                }
            }

            // Update counters
            updateKanbanCounters();

            // Persist to backend
            try {
                await API.updateTask(taskId, { status: targetStatus });
                notifyDataChanged();
            } catch (err) {
                console.error('Failed to update task status via Kanban drop:', err);
            }
        };
    });
}
