// Theme Management
// Handles dark mode toggle and persistence

const themeConfig = {
    darkClass: 'dark-mode',
    storageKey: 'teamtasks-theme',
    toggleBtnId: 'themeToggleBtn'
};

function applyTheme(isDark) {
    if (isDark) {
        document.documentElement.classList.add(themeConfig.darkClass);
    } else {
        document.documentElement.classList.remove(themeConfig.darkClass);
    }
}

function toggleTheme() {
    const isDark = document.documentElement.classList.contains(themeConfig.darkClass);
    const newCtx = !isDark;
    applyTheme(newCtx);
    localStorage.setItem(themeConfig.storageKey, newCtx ? 'dark' : 'light');
    updateIcon(newCtx);
}

const THEME_ICONS = {
    sun: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#555" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-img" aria-hidden="true"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>',
    moon: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#555" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-img" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>'
};

function updateIcon(isDark) {
    const btn = document.getElementById(themeConfig.toggleBtnId);
    if (!btn) return;

    const label = isDark ? 'החלף למצב יום' : 'החלף למצב לילה';
    if (isDark) {
        btn.classList.add('active');
        btn.innerHTML = THEME_ICONS.sun;
    } else {
        btn.classList.remove('active');
        btn.innerHTML = THEME_ICONS.moon;
    }
    btn.title = label;
    btn.setAttribute('aria-label', label);
}

// Init function to be called on page load (inline) and DOMContentLoaded
function initTheme() {
    const stored = localStorage.getItem(themeConfig.storageKey);
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    let isDark = false;
    if (stored === 'dark') {
        isDark = true;
    } else if (stored === 'light') {
        isDark = false;
    } else {
        // Default to system preference if nothing stored? Or defaults to light as per existing?
        // Existing is light. Let's default to light unless user explicitly sets it or system prefers.
        isDark = prefersDark;
    }

    applyTheme(isDark);

    // Defer icon update until DOM is ready if called early
    if (document.readyState === 'loading') {
        window.addEventListener('DOMContentLoaded', () => updateIcon(isDark));
    } else {
        updateIcon(isDark);
    }
}

// Use event delegation so navbar DOM refreshes never break the toggle button
document.addEventListener('click', (e) => {
    const btn = e.target.closest(`#${themeConfig.toggleBtnId}`);
    if (btn) {
        toggleTheme();
    }
});

// Sync icon state when DOM is ready
window.addEventListener('DOMContentLoaded', () => {
    const isDark = document.documentElement.classList.contains(themeConfig.darkClass);
    updateIcon(isDark);
});

// Run immediately to prevent FOUC
initTheme();
