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

function updateIcon(isDark) {
    const btn = document.getElementById(themeConfig.toggleBtnId);
    if (!btn) return;
    // Simple text or icon switch. 
    // Let's assume the button contains an image and we filter it or swap it.
    // For now, toggle a class on the button or icon.
    // Or simpler: The button stays the same "moon" icon, but maybe active state?
    // User asked for "Dark mode toggle button".
    // Let's make the icon look "filled" or "active" if dark.
    if (isDark) {
        btn.classList.add('active');
        btn.innerHTML = '☀️'; // Sun icon for switching to light
        btn.title = 'Switch to Light Mode';
    } else {
        btn.classList.remove('active');
        btn.innerHTML = '🌙'; // Moon icon for switching to dark
        btn.title = 'Switch to Dark Mode';
    }
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

// Attach listener when DOM is ready (for the button)
window.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById(themeConfig.toggleBtnId);
    if (btn) {
        btn.addEventListener('click', toggleTheme);
        // Sync icon state
        const isDark = document.documentElement.classList.contains(themeConfig.darkClass);
        updateIcon(isDark);
    }
});

// Run immediately to prevent FOUC
initTheme();
