// Admin Page JavaScript
document.addEventListener('DOMContentLoaded', () => {
    let teams = [];
    let currentTeam = null;
    let currentMember = null;
    let selectedFile = null;

    // DOM Elements
    const teamsContainer = document.getElementById('teamsContainer');
    const addTeamBtn = document.getElementById('addTeamBtn');
    const teamModal = document.getElementById('teamModal');
    const memberModal = document.getElementById('memberModal');
    const closeModalBtns = document.querySelectorAll('.close-modal, .close-member-modal');
    const saveTeamBtn = document.getElementById('saveTeamBtn');
    const saveMemberBtn = document.getElementById('saveMemberBtn');
    const cancelTeamBtn = document.getElementById('cancelTeamBtn');
    const cancelMemberBtn = document.getElementById('cancelMemberBtn');
    const toast = document.getElementById('toast');

    // Load teams on page load
    loadTeams();

    // Event Listeners
    addTeamBtn.addEventListener('click', () => openTeamModal());
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
            const reader = new FileReader();
            reader.onload = (e) => {
                document.getElementById('avatarPreview').src = e.target.result;
            };
            reader.readAsDataURL(file);
        }
    });

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
                    ${team.members.map(member => `
                        <div class="member-item">
                            <div class="member-info">
                            <img src="/uploads/avatars/${member.avatar_path}" class="member-avatar" alt="${member.name_he}"
                                 onerror="this.src='/static/images/default.png'">
                                <div class="member-names">
                                    <span class="member-name-he">${member.name_he}</span>
                                    <span class="member-name-en">${member.name_en}</span>
                                </div>
                            </div>
                            <div class="member-actions">
                                <button class="btn-icon-small edit-member" data-team-id="${team.id}" data-member-id="${member.id}" title="ערוך">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                                    </svg>
                                </button>
                                <button class="btn-icon-small delete delete-member" data-team-id="${team.id}" data-member-id="${member.id}" title="מחק">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <polyline points="3 6 5 6 21 6"></polyline>
                                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                    </svg>
                                </button>
                            </div>
                        </div>
                    `).join('')}
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

    function openMemberModal(teamId, memberId = null) {
        const team = teams.find(t => t.id === teamId);
        currentTeam = team;
        currentMember = memberId ? team.members.find(m => m.id === memberId) : null;
        selectedFile = null;

        document.getElementById('memberModalTitle').textContent = currentMember ? 'ערוך חבר צוות' : 'הוסף חבר צוות';
        document.getElementById('memberNameEn').value = currentMember ? currentMember.name_en : '';
        document.getElementById('memberNameHe').value = currentMember ? currentMember.name_he : '';

        const avatarPath = currentMember ? `/uploads/avatars/${currentMember.avatar_path}` : '/static/images/default.png';
        document.getElementById('avatarPreview').src = avatarPath;
        document.getElementById('memberAvatar').value = '';

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
                loadTeams();
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
                loadTeams();
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

        try {
            // First, save member data
            const url = currentMember
                ? `/api/teams/${currentTeam.id}/members/${currentMember.id}`
                : `/api/teams/${currentTeam.id}/members`;
            const method = currentMember ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name_en: nameEn, name_he: nameHe })
            });

            const data = await response.json();

            if (data.success) {
                const memberId = currentMember ? currentMember.id : data.member.id;

                // If there's a file selected, upload it
                if (selectedFile) {
                    await uploadAvatar(currentTeam.id, memberId, selectedFile);
                }

                showToast(currentMember ? 'חבר הצוות עודכן בהצלחה' : 'חבר הצוות נוסף בהצלחה', 'success');
                closeModal(memberModal);
                loadTeams();
            } else {
                showToast(data.error || 'שגיאה בשמירת חבר הצוות', 'error');
            }
        } catch (error) {
            showToast('שגיאה בשמירת חבר הצוות', 'error');
            console.error(error);
        }
    }

    async function uploadAvatar(teamId, memberId, file) {
        const formData = new FormData();
        formData.append('avatar', file);

        try {
            const response = await fetch(`/api/teams/${teamId}/members/${memberId}/avatar`, {
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
        if (!confirm('האם אתה בטוח שברצונך למחוק חבר צוות זה?')) {
            return;
        }

        try {
            const response = await fetch(`/api/teams/${teamId}/members/${memberId}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (data.success) {
                showToast('חבר הצוות נמחק בהצלחה', 'success');
                loadTeams();
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
});
