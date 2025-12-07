// Utility functions

export function parseDateToISO(dateStr) {
    if (!dateStr) return null;
    // Expects d/m/Y
    // Normalize separators
    let cleanStr = dateStr.replace(/[\.\-]/g, '/');
    const parts = cleanStr.split('/');
    if (parts.length !== 3) return null;

    // Check for valid date
    const d = new Date(`${parts[2]}-${parts[1]}-${parts[0]}`);
    if (isNaN(d.getTime())) return null;

    return `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`;
}

export function formatDateFromISO(isoStr) {
    if (!isoStr) return '';
    const d = new Date(isoStr);
    if (isNaN(d.getTime())) return '';
    return `${d.getDate()}/${d.getMonth() + 1}/${d.getFullYear()}`;
}

export function getStatusFromClass(className) {
    if (!className) return 'status-notstarted';
    const map = {
        'status-notstarted': 'status-notstarted', // Value matches key for select input usually, or mapped if needed?
        // Wait, the original code mapped styles to text values? 
        // Checking original script: 
        // 'status-notstarted': 'Not Started'
        // But the select options use 'status-notstarted'.
        // Let's check where it's used. openEditModal uses it to set taskStatus.value.
        // The values in HTML select are 'status-notstarted', etc.
        // So this helper should probably return the class name itself if it's valid, or default.
    };

    if (className && className.includes('status-inprogress')) return 'status-inprogress';
    if (className && className.includes('status-done')) return 'status-done';
    if (className && className.includes('status-notstarted')) return 'status-notstarted';
    if (className && className.includes('status-delayed')) return 'status-delayed';

    return 'status-notstarted';
}

// Flatpickr config factory
export function getFlatpickrConfig() {
    return {
        locale: "he",
        dateFormat: "d/m/Y",
        allowInput: true,
        firstDayOfWeek: 0, // Sunday
        disableMobile: "true",
        parseDate: (datestr, format) => {
            if (!datestr) return null;
            let cleanStr = datestr.replace(/[\.\-]/g, '/');
            if (/^\d{8}$/.test(cleanStr)) {
                cleanStr = cleanStr.substring(0, 2) + '/' + cleanStr.substring(2, 4) + '/' + cleanStr.substring(4);
            }
            return flatpickr.parseDate(cleanStr, format);
        }
    };
}
