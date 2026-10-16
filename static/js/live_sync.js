// Live Sync Module - Real-time synchronization across tabs and server
const CHANNEL_NAME = 'teamtasks_live_sync';
let channel = null;

try {
    if (typeof BroadcastChannel !== 'undefined') {
        channel = new BroadcastChannel(CHANNEL_NAME);
    }
} catch (e) {
    console.warn('BroadcastChannel not supported:', e);
}

/**
 * Notify all tabs and the current window that data has changed
 */
export function notifyDataChanged() {
    try {
        if (channel) {
            channel.postMessage({ type: 'teamtasks:data_changed', timestamp: Date.now() });
        }
        window.dispatchEvent(new CustomEvent('teamtasks:refresh'));
        window.dispatchEvent(new CustomEvent('calendar:refresh'));
    } catch (e) {
        console.warn('Failed to broadcast change:', e);
    }
}

// Make accessible globally for non-module scripts
if (typeof window !== 'undefined') {
    window.teamtasksNotifyChange = notifyDataChanged;
}

/**
 * Subscribe a handler to live sync events from other tabs and internal events
 * @param {Function} onRefreshCallback - Function to call when an update is detected
 */
export function subscribeLiveSync(onRefreshCallback) {
    if (channel) {
        channel.onmessage = (event) => {
            if (event.data && event.data.type === 'teamtasks:data_changed') {
                if (typeof onRefreshCallback === 'function') {
                    onRefreshCallback();
                }
            }
        };
    }

    window.addEventListener('teamtasks:refresh', () => {
        if (typeof onRefreshCallback === 'function') {
            onRefreshCallback();
        }
    });
}
