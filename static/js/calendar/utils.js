// Calendar Utils

export function getWeekStart(date) {
    const d = new Date(date);
    const day = d.getDay();
    const diff = day; // Sunday is 0
    d.setDate(d.getDate() - diff);
    d.setHours(0, 0, 0, 0);
    return d;
}

export function formatDateToISO(date) {
    const d = String(date.getDate()).padStart(2, '0');
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const y = date.getFullYear();
    return `${y}-${m}-${d}`; // yyyy-mm-dd
}

export function formatDateDisplay(date) {
    const d = String(date.getDate()).padStart(2, '0');
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const y = date.getFullYear();
    return `${d}/${m}/${y}`;
}

export function parseDateFromISO(isoStr) {
    if (!isoStr) return null;
    const parts = isoStr.split('-');
    if (parts.length !== 3) return null;
    return `${parts[2]}/${parts[1]}/${parts[0]}`; // dd/mm/yyyy
}
