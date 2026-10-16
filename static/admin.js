// Admin Page JavaScript
document.addEventListener('DOMContentLoaded', () => {
    let teams = [];
    let currentTeam = null;
    let currentMember = null;
    let selectedFile = null;
    let selectedPredefinedAvatar = null;
    let predefinedAvatarsCache = null;

    // DOM Elements
    const teamsContainer = document.getElementById('teamsContainer');
    const addTeamBtn = document.getElementById('addTeamBtn');
    const addMemberBtn = document.getElementById('addMemberBtn');
    const teamModal = document.getElementById('teamModal');
    const memberModal = document.getElementById('memberModal');
    const closeModalBtns = document.querySelectorAll('.close-modal, .close-member-modal');
    const saveTeamBtn = document.getElementById('saveTeamBtn');
    const saveMemberBtn = document.getElementById('saveMemberBtn');
    const cancelTeamBtn = document.getElementById('cancelTeamBtn');
    const cancelMemberBtn = document.getElementById('cancelMemberBtn');
    const toast = document.getElementById('toast');

    // Helper to notify other tabs/pages
    function broadcastAdminChange() {
        if (typeof window.teamtasksNotifyChange === 'function') {
            window.teamtasksNotifyChange();
        } else if (typeof BroadcastChannel !== 'undefined') {
            try {
                new BroadcastChannel('teamtasks_live_sync').postMessage({ type: 'teamtasks:data_changed', timestamp: Date.now() });
            } catch (e) {}
        }
    }

    function isAnyAdminModalOpen() {
        return (teamModal && teamModal.style.display === 'block') || (memberModal && memberModal.style.display === 'block');
    }

    let lastAdminVersion = null;
    let isAdminUpdating = false;

    async function checkAdminUpdates() {
        if (isAdminUpdating || isAnyAdminModalOpen()) return;
        try {
            const res = await fetch('/api/version?t=' + Date.now());
            const data = await res.json();
            if (data && typeof data.timestamp !== 'undefined') {
                if (lastAdminVersion === null) {
                    lastAdminVersion = data.timestamp;
                    return;
                }
                if (data.timestamp > lastAdminVersion) {
                    lastAdminVersion = data.timestamp;
                    isAdminUpdating = true;
                    await loadTeams();
                    isAdminUpdating = false;
                }
            }
        } catch (e) {
            isAdminUpdating = false;
        }
    }

    // Load teams on page load
    loadTeams();

    // Start fast polling (every 1.5 seconds)
    setInterval(checkAdminUpdates, 1500);

    // Cross-tab live sync listener
    if (typeof BroadcastChannel !== 'undefined') {
        try {
            const liveChannel = new BroadcastChannel('teamtasks_live_sync');
            liveChannel.onmessage = (event) => {
                if (event.data && event.data.type === 'teamtasks:data_changed') {
                    if (!isAnyAdminModalOpen()) {
                        loadTeams();
                    }
                }
            };
        } catch (e) {}
    }

    window.addEventListener('teamtasks:refresh', () => {
        if (!isAnyAdminModalOpen()) {
            loadTeams();
        }
    });

    // Sidebar Navigation
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.settings-section');

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            // Update Nav
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');

            // Update Section
            const sectionId = 'section-' + item.dataset.section;
            sections.forEach(section => {
                if (section.id === sectionId) {
                    section.classList.add('active');
                } else {
                    section.classList.remove('active');
                }
            });

            if (item.dataset.section === 'system') {
                loadSystemSettings();
            }
        });
    });

    // Backup & Restore
    const downloadBackupBtn = document.getElementById('downloadBackupBtn');
    if (downloadBackupBtn) {
        downloadBackupBtn.addEventListener('click', () => {
            const table = document.getElementById('backupTableSelect').value;
            window.location.href = `/api/backup/${table}`;
        });
    }

    const restoreBtn = document.getElementById('restoreBtn');
    if (restoreBtn) {
        restoreBtn.addEventListener('click', async () => {
            const table = document.getElementById('restoreTableSelect').value;
            const fileInput = document.getElementById('restoreFileInput');
            const files = fileInput.files;

            if (files.length === 0) {
                showToast('נא לבחור קובץ אחד לפחות', 'error');
                return;
            }

            const confirmMsg = table === 'all'
                ? 'אזהרה חמורה: שחזור כל המערכת ימחק את כל הנתונים הקיימים ויחליף אותם בנתוני קובץ הגיבוי! האם להמשיך?'
                : `האם אתה בטוח שברצונך לשחזר נתונים לטבלה "${table}"? פעולה זו תעדכן או תוסיף נתונים מהגיבוי.`;

            if (!confirm(confirmMsg)) {
                return;
            }

            const origHtml = restoreBtn.innerHTML;
            restoreBtn.disabled = true;
            restoreBtn.innerHTML = 'משחזר נתונים...';

            let successCount = 0;
            let errorCount = 0;

            try {
                // Process files sequentially
                for (let i = 0; i < files.length; i++) {
                    const formData = new FormData();
                    formData.append('file', files[i]);

                    try {
                        const response = await fetch(`/api/restore/${table}`, {
                            method: 'POST',
                            body: formData
                        });
                        const result = await response.json();

                        if (result.success) {
                            successCount++;
                        } else {
                            console.error(`Error restoring file ${files[i].name}:`, result.error);
                            errorCount++;
                            showToast(`שגיאה בקובץ ${files[i].name}: ${result.error}`, 'error');
                        }
                    } catch (error) {
                        console.error(error);
                        errorCount++;
                        showToast(`שגיאה בקובץ ${files[i].name}`, 'error');
                    }
                }

                if (successCount > 0) {
                    showToast(`השחזור הושלם: ${successCount} קבצים עובדו בהצלחה`, 'success');
                    if (table === 'teams' || table === 'members' || table === 'projects' || table === 'all') {
                        if (typeof loadTeams === 'function') loadTeams();
                    }
                    if (typeof loadSystemMetrics === 'function') {
                        loadSystemMetrics();
                    }
                    broadcastAdminChange();
                }
            } finally {
                restoreBtn.disabled = false;
                restoreBtn.innerHTML = origHtml;
                fileInput.value = '';
            }
        });
    }

    // Event Listeners
    addTeamBtn.addEventListener('click', () => openTeamModal());
    if (addMemberBtn) addMemberBtn.addEventListener('click', () => openMemberModal());
    saveTeamBtn.addEventListener('click', saveTeam);
    saveMemberBtn.addEventListener('click', saveMember);
    cancelTeamBtn.addEventListener('click', () => closeModal(teamModal));
    cancelMemberBtn.addEventListener('click', () => closeModal(memberModal));

    closeModalBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            closeModal(teamModal);
            closeModal(memberModal);
        });
    });

    // Avatar file input
    document.getElementById('memberAvatar').addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            selectedFile = file;
            selectedPredefinedAvatar = null;
            document.querySelectorAll('#predefinedAvatarsGrid .predefined-avatar-item').forEach(el => el.classList.remove('selected'));
            const reader = new FileReader();
            reader.onload = (e) => {
                document.getElementById('avatarPreview').src = e.target.result;
            };
            reader.readAsDataURL(file);
        }
    });

    async function loadPredefinedAvatars() {
        if (!predefinedAvatarsCache) {
            try {
                const res = await fetch('/api/avatars');
                const data = await res.json();
                if (data.success && Array.isArray(data.avatars) && data.avatars.length > 0) {
                    predefinedAvatarsCache = data.avatars;
                }
            } catch (e) {
                console.error('Failed to fetch predefined avatars:', e);
            }
            if (!predefinedAvatarsCache) {
                predefinedAvatarsCache = Array.from({ length: 12 }, (_, i) => ({
                    id: `avatar_${i + 1}.png`,
                    filename: `avatar_${i + 1}.png`,
                    url: `/static/avatars/avatar_${i + 1}.png`
                }));
            }
        }
        return predefinedAvatarsCache;
    }

    async function renderPredefinedAvatars() {
        const grid = document.getElementById('predefinedAvatarsGrid');
        if (!grid) return;
        const avatars = await loadPredefinedAvatars();
        grid.innerHTML = avatars.map(av => {
            const isSelected = selectedPredefinedAvatar === av.filename;
            return `
                <div class="predefined-avatar-item ${isSelected ? 'selected' : ''}" data-filename="${av.filename}" data-url="${av.url}" title="בחר אווטאר">
                    <img src="${av.url}" alt="${av.filename}">
                    <span class="avatar-check-badge"><i class="fas fa-check"></i></span>
                </div>
            `;
        }).join('');

        grid.querySelectorAll('.predefined-avatar-item').forEach(item => {
            item.addEventListener('click', () => {
                const filename = item.dataset.filename;
                const url = item.dataset.url;
                selectedPredefinedAvatar = filename;
                selectedFile = null;
                document.getElementById('memberAvatar').value = '';
                document.getElementById('avatarPreview').src = url;

                grid.querySelectorAll('.predefined-avatar-item').forEach(el => el.classList.remove('selected'));
                item.classList.add('selected');
            });
        });
    }

    // Close modals on outside click
    window.addEventListener('click', (e) => {
        if (e.target === teamModal) closeModal(teamModal);
        if (e.target === memberModal) closeModal(memberModal);
    });

    // Functions
    async function loadTeams() {
        try {
            const response = await fetch('/api/teams');
            teams = await response.json();
            renderTeams();
        } catch (error) {
            showToast('שגיאה בטעינת צוותים', 'error');
            console.error(error);
        }
    }

    function renderTeams() {
        if (teams.length === 0) {
            teamsContainer.innerHTML = `
                <div class="empty-state">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                        <circle cx="9" cy="7" r="4"></circle>
                        <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                        <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                    </svg>
                    <h3>אין צוותים במערכת</h3>
                    <p>לחץ על "הוסף צוות חדש" כדי להתחיל</p>
                </div>
            `;
            return;
        }

        teamsContainer.innerHTML = teams.map(team => `
            <div class="team-card" data-team-id="${team.id}">
                <div class="team-card-header">
                    <div>
                        <span class="team-name">${team.name_he}</span>
                        <span class="team-name-en">(${team.name_en})</span>
                    </div>
                    <div class="team-actions">
                        <button class="btn-icon-small edit-team" data-team-id="${team.id}" title="ערוך צוות">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                            </svg>
                        </button>
                        <button class="btn-icon-small delete delete-team" data-team-id="${team.id}" title="מחק צוות">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="3 6 5 6 21 6"></polyline>
                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                            </svg>
                        </button>
                    </div>
                </div>
                <div class="members-list">
                    <div class="members-list-header">
                        <span class="members-list-title">חברי צוות (${team.members.length})</span>
                        <button class="btn btn-small btn-primary add-member" data-team-id="${team.id}">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
                            </svg>
                            הוסף חבר
                        </button>
                    </div>
                    ${team.members.length === 0 ? '<p style="color: #9ca3af; font-size: 0.875rem;">אין חברי צוות</p>' : ''}
                    ${team.members.map(member => {
                        const otherTeams = (member.teams || []).filter(t => t.id !== team.id);
                        const otherTeamsHtml = otherTeams.length > 0 ? `
                            <div class="member-other-teams">
                                ${otherTeams.map(t => `<span class="team-badge-pill" title="משויך גם לצוות ${t.name_he}">${t.name_he}</span>`).join('')}
                            </div>
                        ` : '';
                        return `
                        <div class="member-item">
                            <div class="member-info">
                            <img src="/uploads/avatars/${member.avatar_path}" class="member-avatar" alt="${member.name_he}"
                                 onerror="this.src='/static/images/default.png'">
                                <div class="member-names">
                                    <span class="member-name-he">${member.name_he}</span>
                                    <span class="member-name-en">${member.name_en}</span>
                                    ${otherTeamsHtml}
                                </div>
                            </div>
                            <div class="member-actions">
                                <button class="btn-icon-small edit-member" data-team-id="${team.id}" data-member-id="${member.id}" title="ערוך חבר צוות ושיוך לצוותים">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                                    </svg>
                                </button>
                                <button class="btn-icon-small delete delete-member" data-team-id="${team.id}" data-member-id="${member.id}" title="${otherTeams.length > 0 ? 'הסר מצוות זה' : 'מחק חבר צוות'}">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <polyline points="3 6 5 6 21 6"></polyline>
                                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                    </svg>
                                </button>
                            </div>
                        </div>
                    `;}).join('')}
                </div>
            </div>
        `).join('');

        // Attach event listeners to dynamically created elements
        attachEventListeners();
    }

    function attachEventListeners() {
        // Edit team buttons
        document.querySelectorAll('.edit-team').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const teamId = parseInt(btn.dataset.teamId);
                openTeamModal(teamId);
            });
        });

        // Delete team buttons
        document.querySelectorAll('.delete-team').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const teamId = parseInt(btn.dataset.teamId);
                deleteTeam(teamId);
            });
        });

        // Add member buttons
        document.querySelectorAll('.add-member').forEach(btn => {
            btn.addEventListener('click', () => {
                const teamId = parseInt(btn.dataset.teamId);
                openMemberModal(teamId);
            });
        });

        // Edit member buttons
        document.querySelectorAll('.edit-member').forEach(btn => {
            btn.addEventListener('click', () => {
                const teamId = parseInt(btn.dataset.teamId);
                const memberId = parseInt(btn.dataset.memberId);
                openMemberModal(teamId, memberId);
            });
        });

        // Delete member buttons
        document.querySelectorAll('.delete-member').forEach(btn => {
            btn.addEventListener('click', () => {
                const teamId = parseInt(btn.dataset.teamId);
                const memberId = parseInt(btn.dataset.memberId);
                deleteMember(teamId, memberId);
            });
        });
    }

    function openTeamModal(teamId = null) {
        currentTeam = teamId ? teams.find(t => t.id === teamId) : null;

        document.getElementById('teamModalTitle').textContent = currentTeam ? 'ערוך צוות' : 'הוסף צוות חדש';
        document.getElementById('teamNameEn').value = currentTeam ? currentTeam.name_en : '';
        document.getElementById('teamNameHe').value = currentTeam ? currentTeam.name_he : '';

        teamModal.style.display = 'block';
    }

    function openMemberModal(teamId = null, memberId = null) {
        let member = null;
        if (memberId) {
            for (const t of teams) {
                const found = (t.members || []).find(m => m.id === memberId);
                if (found) {
                    member = found;
                    break;
                }
            }
        }
        currentTeam = teamId ? teams.find(t => t.id === teamId) : null;
        currentMember = member;
        selectedFile = null;
        selectedPredefinedAvatar = null;

        document.getElementById('memberModalTitle').textContent = currentMember ? 'ערוך חבר צוות' : 'הוסף חבר צוות';
        document.getElementById('memberNameEn').value = currentMember ? currentMember.name_en : '';
        document.getElementById('memberNameHe').value = currentMember ? currentMember.name_he : '';

        if (currentMember && currentMember.avatar_path && currentMember.avatar_path.startsWith('avatar_')) {
            selectedPredefinedAvatar = currentMember.avatar_path;
        }

        const avatarPath = currentMember ? `/uploads/avatars/${currentMember.avatar_path}` : '/static/images/default.png';
        document.getElementById('avatarPreview').src = avatarPath;
        document.getElementById('memberAvatar').value = '';

        renderPredefinedAvatars();

        // Populate team checkboxes
        const memberTeamsContainer = document.getElementById('memberTeamsContainer');
        if (memberTeamsContainer) {
            const memberTeamIds = new Set();
            if (currentMember) {
                if (Array.isArray(currentMember.team_ids)) {
                    currentMember.team_ids.forEach(id => memberTeamIds.add(id));
                } else if (Array.isArray(currentMember.teams)) {
                    currentMember.teams.forEach(t => memberTeamIds.add(t.id));
                } else if (currentMember.team_id) {
                    memberTeamIds.add(currentMember.team_id);
                }
            } else if (teamId) {
                memberTeamIds.add(teamId);
            } else if (teams.length === 1) {
                memberTeamIds.add(teams[0].id);
            }

            memberTeamsContainer.innerHTML = teams.map(t => {
                const isChecked = memberTeamIds.has(t.id);
                return `
                    <label class="team-checkbox-card ${isChecked ? 'checked' : ''}">
                        <input type="checkbox" name="memberTeams" value="${t.id}" ${isChecked ? 'checked' : ''}>
                        <span class="team-checkbox-label" title="${t.name_he}">${t.name_he} <span class="team-checkbox-en">(${t.name_en})</span></span>
                    </label>
                `;
            }).join('');

            memberTeamsContainer.querySelectorAll('input[name="memberTeams"]').forEach(input => {
                input.addEventListener('change', (e) => {
                    const card = e.target.closest('.team-checkbox-card');
                    if (card) {
                        if (e.target.checked) card.classList.add('checked');
                        else card.classList.remove('checked');
                    }
                });
            });
        }

        memberModal.style.display = 'block';
    }

    function closeModal(modal) {
        modal.style.display = 'none';
        currentTeam = null;
        currentMember = null;
        selectedFile = null;
    }

    async function saveTeam() {
        const nameEn = document.getElementById('teamNameEn').value.trim().toLowerCase();
        const nameHe = document.getElementById('teamNameHe').value.trim();

        if (!nameEn || !nameHe) {
            showToast('נא למלא את כל השדות', 'error');
            return;
        }

        try {
            const url = currentTeam ? `/api/teams/${currentTeam.id}` : '/api/teams';
            const method = currentTeam ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name_en: nameEn, name_he: nameHe })
            });

            const data = await response.json();

            if (data.success) {
                showToast(currentTeam ? 'הצוות עודכן בהצלחה' : 'הצוות נוצר בהצלחה', 'success');
                closeModal(teamModal);
                await loadTeams();
                broadcastAdminChange();
            } else {
                showToast(data.error || 'שגיאה בשמירת הצוות', 'error');
            }
        } catch (error) {
            showToast('שגיאה בשמירת הצוות', 'error');
            console.error(error);
        }
    }

    async function deleteTeam(teamId) {
        if (!confirm('האם אתה בטוח שברצונך למחוק צוות זה? פעולה זו תמחק גם את כל חברי הצוות.')) {
            return;
        }

        try {
            const response = await fetch(`/api/teams/${teamId}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (data.success) {
                showToast('הצוות נמחק בהצלחה', 'success');
                await loadTeams();
                broadcastAdminChange();
            } else {
                showToast('שגיאה במחיקת הצוות', 'error');
            }
        } catch (error) {
            showToast('שגיאה במחיקת הצוות', 'error');
            console.error(error);
        }
    }

    async function saveMember() {
        const nameEn = document.getElementById('memberNameEn').value.trim().toLowerCase();
        const nameHe = document.getElementById('memberNameHe').value.trim();

        if (!nameEn || !nameHe) {
            showToast('נא למלא את כל השדות', 'error');
            return;
        }

        const checkedBoxes = Array.from(document.querySelectorAll('input[name="memberTeams"]:checked'));
        const selectedTeamIds = checkedBoxes.map(cb => parseInt(cb.value)).filter(id => !isNaN(id));

        if (selectedTeamIds.length === 0) {
            showToast('יש לבחור לפחות צוות אחד', 'error');
            return;
        }

        try {
            const url = currentMember
                ? `/api/members/${currentMember.id}`
                : `/api/members`;
            const method = currentMember ? 'PUT' : 'POST';

            const payload = { 
                name_en: nameEn, 
                name_he: nameHe,
                team_ids: selectedTeamIds
            };
            if (selectedPredefinedAvatar && !selectedFile) {
                payload.avatar_path = selectedPredefinedAvatar;
            }

            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (data.success) {
                const memberId = currentMember ? currentMember.id : data.member.id;

                // If there's a file selected, upload it
                if (selectedFile) {
                    await uploadAvatar(memberId, selectedFile);
                }

                showToast(currentMember ? 'חבר הצוות עודכן בהצלחה' : 'חבר הצוות נוסף בהצלחה', 'success');
                closeModal(memberModal);
                await loadTeams();
                broadcastAdminChange();
            } else {
                showToast(data.error || 'שגיאה בשמירת חבר הצוות', 'error');
            }
        } catch (error) {
            showToast('שגיאה בשמירת חבר הצוות', 'error');
            console.error(error);
        }
    }

    async function uploadAvatar(memberId, file) {
        const formData = new FormData();
        formData.append('avatar', file);

        try {
            const response = await fetch(`/api/members/${memberId}/avatar`, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!data.success) {
                showToast('שגיאה בהעלאת התמונה', 'error');
            }
        } catch (error) {
            showToast('שגיאה בהעלאת התמונה', 'error');
            console.error(error);
        }
    }

    async function deleteMember(teamId, memberId) {
        let member = null;
        const team = teams.find(t => t.id === teamId);
        if (team) {
            member = (team.members || []).find(m => m.id === memberId);
        }

        const isMultiTeam = member && member.teams && member.teams.length > 1;
        const confirmMsg = isMultiTeam
            ? `האם להסיר את "${member.name_he}" מצוות "${team.name_he}"? (חבר הצוות משויך לצוותים נוספים ויישאר בהם)`
            : `האם אתה בטוח שברצונך למחוק את חבר הצוות "${member ? member.name_he : ''}"?`;

        if (!confirm(confirmMsg)) {
            return;
        }

        try {
            const response = await fetch(`/api/teams/${teamId}/members/${memberId}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (data.success) {
                showToast(isMultiTeam ? 'חבר הצוות הוסר מהצוות בהצלחה' : 'חבר הצוות נמחק בהצלחה', 'success');
                await loadTeams();
                broadcastAdminChange();
            } else {
                showToast('שגיאה במחיקת חבר הצוות', 'error');
            }
        } catch (error) {
            showToast('שגיאה במחיקת חבר הצוות', 'error');
            console.error(error);
        }
    }

    function showToast(message, type = 'success') {
        toast.textContent = message;
        toast.className = `toast show ${type}`;

        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }

    // --- General System & Environment Settings ---
    let systemSettingsLoaded = false;

    async function loadSystemSettings() {
        try {
            const res = await fetch('/api/system/settings?t=' + Date.now());
            const data = await res.json();
            if (!data.success) {
                showToast(data.error || 'שגיאה בטעינת הגדרות המערכת', 'error');
                return;
            }

            const { settings, ai_status, system_info } = data;

            // 1. AI Provider Radios
            const currentProvider = settings.ai_provider || ai_status.provider || 'cloudflare';
            const radioLocal = document.getElementById('radioProviderLocal');
            const radioCloudflare = document.getElementById('radioProviderCloudflare');

            if (currentProvider === 'local_openai') {
                if (radioLocal) radioLocal.checked = true;
                updateProviderCardSelection('local_openai');
            } else {
                if (radioCloudflare) radioCloudflare.checked = true;
                updateProviderCardSelection('cloudflare');
            }

            // 2. Populate Local Fields
            const inputOpenAiBaseUrl = document.getElementById('inputOpenAiBaseUrl');
            const inputOpenAiModel = document.getElementById('inputOpenAiModel');
            const inputOpenAiApiKey = document.getElementById('inputOpenAiApiKey');
            if (inputOpenAiBaseUrl) inputOpenAiBaseUrl.value = settings.openai_base_url || '';
            if (inputOpenAiModel) inputOpenAiModel.value = settings.openai_model || 'llama3.3';
            if (inputOpenAiApiKey) {
                inputOpenAiApiKey.value = settings.has_openai_key ? (settings.openai_api_key_masked || '••••••••••••••••') : '';
            }

            // 3. Populate Cloudflare Fields
            const inputCfAccountId = document.getElementById('inputCfAccountId');
            const inputCfModel = document.getElementById('inputCfModel');
            const inputCfApiToken = document.getElementById('inputCfApiToken');
            const hintCfTokenStatus = document.getElementById('hintCfTokenStatus');
            if (inputCfAccountId) inputCfAccountId.value = settings.cloudflare_account_id || '';
            if (inputCfModel) inputCfModel.value = settings.cloudflare_model || '@cf/meta/llama-3.1-8b-instruct';
            if (inputCfApiToken) {
                if (settings.has_cloudflare_token) {
                    inputCfApiToken.value = settings.cloudflare_api_token_masked || '••••••••••••••••';
                    if (hintCfTokenStatus) hintCfTokenStatus.textContent = 'מפתח API קיים ושמור במערכת. הזן מפתח חדש רק במידה שברצונך להחליפו.';
                } else {
                    inputCfApiToken.value = '';
                    if (hintCfTokenStatus) hintCfTokenStatus.textContent = 'לא הוגדר מפתח API עבור Cloudflare. אנא הזן מפתח.';
                }
            }

            // 4. Update AI Status Badges
            updateAiBadges(ai_status);

            // 5. Populate System Metrics
            if (system_info && system_info.metrics) {
                const m = system_info.metrics;
                const statTasksCount = document.getElementById('statTasksCount');
                const statTasksSub = document.getElementById('statTasksSub');
                const statProjectsCount = document.getElementById('statProjectsCount');
                const statProjectsSub = document.getElementById('statProjectsSub');
                const statTeamsCount = document.getElementById('statTeamsCount');
                const statMembersCount = document.getElementById('statMembersCount');
                const statDbSize = document.getElementById('statDbSize');

                if (statTasksCount) statTasksCount.textContent = m.total_tasks || 0;
                if (statTasksSub) statTasksSub.textContent = `${m.done_tasks || 0} הושלמו · ${m.inprogress_tasks || 0} בתהליך`;
                if (statProjectsCount) statProjectsCount.textContent = m.total_projects || 0;
                if (statProjectsSub) statProjectsSub.textContent = `${m.active_projects || 0} פעילים · ${m.archived_projects || 0} בארכיון`;
                if (statTeamsCount) statTeamsCount.textContent = m.total_teams || 0;
                if (statMembersCount) statMembersCount.textContent = `${m.total_members || 0} חברי צוות`;
                if (statDbSize) statDbSize.textContent = system_info.db_size || '--';
            }

            // 6. Storage & Runtime info
            if (system_info) {
                const infoDbPath = document.getElementById('infoDbPath');
                const infoUploadsSummary = document.getElementById('infoUploadsSummary');
                const infoPlatform = document.getElementById('infoPlatform');
                const infoPythonVersion = document.getElementById('infoPythonVersion');

                if (infoDbPath) infoDbPath.textContent = system_info.db_path || 'tasks.db';
                if (infoUploadsSummary && system_info.uploads) {
                    infoUploadsSummary.textContent = `${system_info.uploads.count || 0} תמונות (${system_info.uploads.size || '0 KB'})`;
                }
                if (infoPlatform && system_info.runtime) {
                    infoPlatform.textContent = `${system_info.runtime.platform || 'Unknown'} (Debug: ${system_info.runtime.debug ? 'פעיל' : 'כבוי'})`;
                }
                if (infoPythonVersion && system_info.runtime) {
                    infoPythonVersion.textContent = system_info.runtime.python_version || '--';
                }
            }

            systemSettingsLoaded = true;
        } catch (e) {
            console.error('Error loading system settings:', e);
            showToast('שגיאה בתקשורת עם השרת בעת טעינת הגדרות', 'error');
        }
    }

    function updateAiBadges(ai_status) {
        const badgeStatus = document.getElementById('badgeAiStatus');
        const badgeProvider = document.getElementById('badgeAiProvider');
        const badgeAirgap = document.getElementById('badgeAirgap');

        if (!badgeStatus) return;

        if (ai_status && ai_status.configured) {
            badgeStatus.textContent = '● פעיל ומחובר';
            badgeStatus.className = 'status-pill status-pill-success';
        } else {
            badgeStatus.textContent = '● אינו מוגדר';
            badgeStatus.className = 'status-pill status-pill-warning';
        }

        if (badgeProvider) {
            badgeProvider.textContent = (ai_status && ai_status.name) ? ai_status.name : ((ai_status && ai_status.provider === 'local_openai') ? 'Local OpenAI Gateway' : 'Cloudflare Workers AI');
        }

        if (badgeAirgap) {
            if (ai_status && ai_status.is_airgapped) {
                badgeAirgap.textContent = '🛡️ שער מקומי מבודד (Airgapped)';
                badgeAirgap.className = 'status-pill status-pill-airgap';
            } else {
                badgeAirgap.textContent = '☁️ ענן (Cloudflare)';
                badgeAirgap.className = 'status-pill status-pill-cloud';
            }
        }
    }

    function updateProviderCardSelection(provider) {
        const cardLocal = document.getElementById('cardProviderLocal');
        const cardCloudflare = document.getElementById('cardProviderCloudflare');
        const boxLocal = document.getElementById('boxLocalAiFields');
        const boxCloudflare = document.getElementById('boxCloudflareFields');

        if (provider === 'local_openai') {
            if (cardLocal) cardLocal.classList.add('selected');
            if (cardCloudflare) cardCloudflare.classList.remove('selected');
            if (boxLocal) boxLocal.style.display = 'block';
            if (boxCloudflare) boxCloudflare.style.display = 'none';
        } else {
            if (cardCloudflare) cardCloudflare.classList.add('selected');
            if (cardLocal) cardLocal.classList.remove('selected');
            if (boxLocal) boxLocal.style.display = 'none';
            if (boxCloudflare) boxCloudflare.style.display = 'block';
        }
    }

    // Provider radio switch event listeners
    document.querySelectorAll('input[name="ai_provider_radio"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            updateProviderCardSelection(e.target.value);
        });
    });

    // Password visibility toggle buttons
    document.querySelectorAll('.btn-toggle-visibility').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.dataset.target;
            const input = document.getElementById(targetId);
            if (!input) return;
            if (input.type === 'password') {
                input.type = 'text';
                btn.textContent = '🔒';
            } else {
                input.type = 'password';
                btn.textContent = '👁️';
            }
        });
    });

    // Save System Settings
    const btnSaveSystemSettings = document.getElementById('btnSaveSystemSettings');
    if (btnSaveSystemSettings) {
        btnSaveSystemSettings.addEventListener('click', async () => {
            const selectedRadio = document.querySelector('input[name="ai_provider_radio"]:checked');
            const provider = selectedRadio ? selectedRadio.value : 'cloudflare';

            const payload = {
                ai_provider: provider,
                openai_base_url: document.getElementById('inputOpenAiBaseUrl')?.value.trim() || '',
                openai_model: document.getElementById('inputOpenAiModel')?.value.trim() || 'llama3.3',
                openai_api_key: document.getElementById('inputOpenAiApiKey')?.value.trim() || '',
                cloudflare_account_id: document.getElementById('inputCfAccountId')?.value.trim() || '',
                cloudflare_model: document.getElementById('inputCfModel')?.value.trim() || '@cf/meta/llama-3.1-8b-instruct',
                cloudflare_api_token: document.getElementById('inputCfApiToken')?.value.trim() || ''
            };

            btnSaveSystemSettings.disabled = true;
            btnSaveSystemSettings.textContent = 'שומר...';

            try {
                const res = await fetch('/api/system/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const result = await res.json();
                if (result.success) {
                    showToast('ההגדרות נשמרו בהצלחה בקובץ .env ומנוע ה-AI עודכן!', 'success');
                    if (result.ai_status) {
                        updateAiBadges(result.ai_status);
                    }
                    await loadSystemSettings();
                } else {
                    showToast(result.error || 'שגיאה בשמירת ההגדרות', 'error');
                }
            } catch (err) {
                console.error(err);
                showToast('שגיאת תקשורת עם השרת', 'error');
            } finally {
                btnSaveSystemSettings.disabled = false;
                btnSaveSystemSettings.innerHTML = `<img src="/static/icons/save.svg" width="18" height="18" style="vertical-align:middle; filter: brightness(0) invert(1);"> שמור הגדרות`;
            }
        });
    }

    // Test AI Connection
    const btnTestAiConnection = document.getElementById('btnTestAiConnection');
    const testAiSpinner = document.getElementById('testAiSpinner');
    const testAiBtnText = document.getElementById('testAiBtnText');
    const aiTestResultBox = document.getElementById('aiTestResultBox');
    const testResultTitle = document.getElementById('testResultTitle');
    const testResultDetails = document.getElementById('testResultDetails');
    const testResultIcon = document.getElementById('testResultIcon');

    if (btnTestAiConnection) {
        btnTestAiConnection.addEventListener('click', async () => {
            const selectedRadio = document.querySelector('input[name="ai_provider_radio"]:checked');
            const provider = selectedRadio ? selectedRadio.value : 'cloudflare';

            const payload = {
                ai_provider: provider,
                openai_base_url: document.getElementById('inputOpenAiBaseUrl')?.value.trim() || '',
                openai_model: document.getElementById('inputOpenAiModel')?.value.trim() || '',
                openai_api_key: document.getElementById('inputOpenAiApiKey')?.value.trim() || '',
                cloudflare_account_id: document.getElementById('inputCfAccountId')?.value.trim() || '',
                cloudflare_model: document.getElementById('inputCfModel')?.value.trim() || '',
                cloudflare_api_token: document.getElementById('inputCfApiToken')?.value.trim() || ''
            };

            btnTestAiConnection.disabled = true;
            if (testAiSpinner) testAiSpinner.style.display = 'inline-block';
            if (testAiBtnText) testAiBtnText.textContent = 'בודק חיבור...';
            if (aiTestResultBox) aiTestResultBox.style.display = 'none';

            try {
                const res = await fetch('/api/system/test-ai', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const result = await res.json();

                if (aiTestResultBox) {
                    aiTestResultBox.style.display = 'flex';
                    if (result.success) {
                        aiTestResultBox.className = 'test-result-box success';
                        if (testResultIcon) testResultIcon.textContent = '✓';
                        if (testResultTitle) testResultTitle.textContent = `חיבור תקין בהצלחה! (זמן תגובה: ${result.latency_ms}ms)`;
                        if (testResultDetails) {
                            const provText = result.is_airgapped ? 'שער מקומי מבודד (Airgapped)' : 'Cloudflare Workers AI';
                            testResultDetails.innerHTML = `<strong>ספק:</strong> ${provText} | <strong>מודל:</strong> <code>${result.model}</code> | <strong>תשובה:</strong> <em>${result.reply || 'OK'}</em>`;
                        }
                    } else {
                        aiTestResultBox.className = 'test-result-box error';
                        if (testResultIcon) testResultIcon.textContent = '✕';
                        if (testResultTitle) testResultTitle.textContent = `בדיקת החיבור נכשלה! (${result.latency_ms || 0}ms)`;
                        if (testResultDetails) testResultDetails.textContent = result.error || 'שגיאה לא מזוהה בעת יצירת קשר עם המודל.';
                    }
                }
            } catch (err) {
                console.error(err);
                if (aiTestResultBox) {
                    aiTestResultBox.style.display = 'flex';
                    aiTestResultBox.className = 'test-result-box error';
                    if (testResultIcon) testResultIcon.textContent = '✕';
                    if (testResultTitle) testResultTitle.textContent = 'שגיאת רשת בבדיקת החיבור';
                    if (testResultDetails) testResultDetails.textContent = err.message || 'לא ניתן לתקשר עם שרת האפליקציה.';
                }
            } finally {
                btnTestAiConnection.disabled = false;
                if (testAiSpinner) testAiSpinner.style.display = 'none';
                if (testAiBtnText) testAiBtnText.textContent = 'בדיקת חיבור מודל';
            }
        });
    }

    const btnDismissTestResult = document.getElementById('btnDismissTestResult');
    if (btnDismissTestResult && aiTestResultBox) {
        btnDismissTestResult.addEventListener('click', () => {
            aiTestResultBox.style.display = 'none';
        });
    }

    // Refresh System button
    const btnRefreshSystem = document.getElementById('btnRefreshSystem');
    if (btnRefreshSystem) {
        btnRefreshSystem.addEventListener('click', async () => {
            btnRefreshSystem.disabled = true;
            await loadSystemSettings();
            showToast('נתוני המערכת רועננו בהצלחה', 'info');
            btnRefreshSystem.disabled = false;
        });
    }

    // Check DB Integrity
    const btnCheckDbIntegrity = document.getElementById('btnCheckDbIntegrity');
    const dbIntegrityResult = document.getElementById('dbIntegrityResult');
    if (btnCheckDbIntegrity) {
        btnCheckDbIntegrity.addEventListener('click', async () => {
            btnCheckDbIntegrity.disabled = true;
            btnCheckDbIntegrity.textContent = 'בודק...';
            if (dbIntegrityResult) dbIntegrityResult.textContent = '';
            try {
                const res = await fetch('/api/system/check-db', { method: 'POST' });
                const data = await res.json();
                if (dbIntegrityResult) {
                    if (data.success && data.integrity === 'ok') {
                        dbIntegrityResult.textContent = '✓ מסד הנתונים תקין לחלוטין (ok)';
                        dbIntegrityResult.style.color = '#10b981';
                    } else {
                        dbIntegrityResult.textContent = `סטטוס: ${data.integrity || data.error}`;
                        dbIntegrityResult.style.color = '#ef4444';
                    }
                }
            } catch (e) {
                if (dbIntegrityResult) {
                    dbIntegrityResult.textContent = 'שגיאה בבדיקה';
                    dbIntegrityResult.style.color = '#ef4444';
                }
            } finally {
                btnCheckDbIntegrity.disabled = false;
                btnCheckDbIntegrity.textContent = 'בדוק שלמות מסד נתונים (Integrity Check)';
            }
        });
    }

    const navTasks = document.getElementById('navTasksLink');
    if (navTasks) {
        navTasks.addEventListener('click', (e) => {
            const storedTeam = localStorage.getItem('activeTeamFilter');
            if (storedTeam === 'archive') {
                e.preventDefault();
                window.location.href = '/?mode=archive';
            } else if (storedTeam) {
                e.preventDefault();
                window.location.href = `/?team=${encodeURIComponent(storedTeam)}`;
            }
        });
    }
});
