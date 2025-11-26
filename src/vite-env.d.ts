/// <reference types="svelte" />
/// <reference types="vite/client" />

declare module 'virtual:build-info' {
    export const buildInfo: { buildDate: string };
}

declare module 'svelte-leafletjs';
