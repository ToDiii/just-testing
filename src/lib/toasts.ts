import { writable } from 'svelte/store';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface Toast {
    id: number;
    type: ToastType;
    message: string;
    duration?: number; // ms, default 4000
}

let nextId = 0;
export const toasts = writable<Toast[]>([]);

export function addToast(message: string, type: ToastType = 'info', duration = 4000) {
    const id = ++nextId;
    toasts.update(t => [...t, { id, type, message, duration }]);
    setTimeout(() => removeToast(id), duration);
    return id;
}

export function removeToast(id: number) {
    toasts.update(t => t.filter(toast => toast.id !== id));
}

export const toast = {
    success: (msg: string, duration?: number) => addToast(msg, 'success', duration),
    error: (msg: string, duration?: number) => addToast(msg, 'error', duration ?? 6000),
    info: (msg: string, duration?: number) => addToast(msg, 'info', duration),
    warning: (msg: string, duration?: number) => addToast(msg, 'warning', duration),
};
