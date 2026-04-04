<script lang="ts">
    import { onMount } from "svelte";
    import { api } from "../api";
    import { t, language } from "../stores";
    import { toast } from "../toasts";

    interface NotificationConfig {
        id: number;
        type: string;
        recipient: string;
        enabled: boolean;
    }

    let scrapingConfig = {
        max_html_links: 15,
        max_pdf_links: 10,
        request_delay: 0.5,
        scraper_engine: "requests",
        crawl4ai_server_url: "",
        crawl4ai_fallback: true,
        max_targets_per_run: 500,
    };

    let notificationConfigs: NotificationConfig[] = [];
    let newNotification = {
        type: "webhook",
        recipient: "",
        enabled: true,
    };

    let isLoading = false;

    // Crawl4AI connection test
    type TestResult = { ok: boolean; message: string; latency_ms?: number; detail?: string; response?: any } | null;
    let crawl4aiTestResult: TestResult = null;
    let crawl4aiTesting = false;

    // AI config
    let aiConfig = {
        provider: "openrouter",
        api_key: "",
        base_url: "",
        model_name: "openai/gpt-4o-mini",
        system_prompt: "",
        enabled: true,
    };
    let aiConfigLoaded = false;

    onMount(async () => {
        await loadConfigs();
        await loadAiConfig();
    });

    async function loadConfigs() {
        isLoading = true;
        try {
            scrapingConfig = await api("/api/config/scraping");
            notificationConfigs = await api("/api/notifications/config");
        } catch (error: any) {
            console.error("Error loading configs:", error);
        } finally {
            isLoading = false;
        }
    }

    async function testCrawl4aiConnection() {
        crawl4aiTesting = true;
        crawl4aiTestResult = null;
        try {
            const serverUrl = scrapingConfig.crawl4ai_server_url?.trim() || "";
            const params = serverUrl ? `?server_url=${encodeURIComponent(serverUrl)}` : "";
            crawl4aiTestResult = await api(`/api/crawl4ai/test${params}`);
        } catch (error: any) {
            crawl4aiTestResult = { ok: false, message: error.message };
        } finally {
            crawl4aiTesting = false;
        }
    }

    async function saveScrapingConfig() {
        isLoading = true;
        try {
            await api("/api/config/scraping", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(scrapingConfig),
            });
            toast.success($language === "de" ? "Scraping-Konfiguration gespeichert!" : "Scraping configuration saved!");
        } catch (error: any) {
            toast.error(($language === "de" ? "Fehler: " : "Error: ") + error.message);
        } finally {
            isLoading = false;
        }
    }

    async function addNotification() {
        if (!newNotification.recipient) return;
        isLoading = true;
        try {
            await api("/api/notifications/config", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(newNotification),
            });
            newNotification.recipient = "";
            await loadConfigs();
            toast.success($language === "de" ? "Benachrichtigungskanal hinzugefügt!" : "Notification channel added!");
        } catch (error: any) {
            toast.error(error.message);
        } finally {
            isLoading = false;
        }
    }

    async function deleteNotification(id: number) {
        isLoading = true;
        try {
            await api(`/api/notifications/config/${id}`, { method: "DELETE" });
            await loadConfigs();
            toast.info($language === "de" ? "Kanal gelöscht." : "Channel deleted.");
        } catch (error: any) {
            toast.error(error.message);
        } finally {
            isLoading = false;
        }
    }

    async function loadAiConfig() {
        try {
            const cfg = await api("/api/ai/config");
            if (cfg) {
                aiConfig = { ...aiConfig, ...cfg };
            }
            aiConfigLoaded = true;
        } catch (error: any) {
            console.error("Error loading AI config:", error);
            aiConfigLoaded = true;
        }
    }

    async function saveAiConfig() {
        isLoading = true;
        try {
            await api("/api/ai/config", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(aiConfig),
            });
            toast.success($language === "de" ? "KI-Einstellungen gespeichert!" : "AI settings saved!");
        } catch (error: any) {
            toast.error(($language === "de" ? "Fehler: " : "Error: ") + error.message);
        } finally {
            isLoading = false;
        }
    }

    async function testNotification(id: number) {
        isLoading = true;
        try {
            const result = await api(`/api/notifications/test/${id}`, { method: "POST" });
            toast.success(result.message || ($language === "de" ? "Test-Benachrichtigung gesendet!" : "Test notification sent!"));
        } catch (error: any) {
            toast.error(($language === "de" ? "Fehler: " : "Error: ") + error.message);
        } finally {
            isLoading = false;
        }
    }
</script>

<div class="p-6 bg-white rounded-lg shadow-md">
    <h2 class="text-2xl font-bold mb-6">{$t("admin_dashboard")}</h2>

    <section class="mb-8 border-b pb-8">
        <h3 class="text-xl font-semibold mb-4 flex items-center">
            <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-6 w-6 mr-2 text-indigo-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
            >
                <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"
                />
            </svg>
            {$t("scraping_limits")}
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div class="space-y-1">
                <label class="block text-sm font-semibold text-gray-700"
                    >{$t("max_html_links")}</label
                >
                <input
                    type="number"
                    bind:value={scrapingConfig.max_html_links}
                    class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
                <p class="text-xs text-gray-500 mt-2 italic">
                    {$language === "de"
                        ? "Maximale Unterseiten pro Kommune. Höhere Werte erhöhen die Tiefe, dauern aber länger."
                        : "The maximum number of subpages to crawl per municipality. Higher values increase depth but take longer."}
                </p>
            </div>
            <div class="space-y-1">
                <label class="block text-sm font-semibold text-gray-700"
                    >{$t("max_pdf_links")}</label
                >
                <input
                    type="number"
                    bind:value={scrapingConfig.max_pdf_links}
                    class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
                <p class="text-xs text-gray-500 mt-2 italic">
                    {$language === "de"
                        ? "Maximale Anzahl relevanter PDF-Dokumente pro Website."
                        : "Maximum number of relevant PDF documents to analyze per site."}
                </p>
            </div>
            <div class="space-y-1">
                <label class="block text-sm font-semibold text-gray-700"
                    >{$t("request_delay")}</label
                >
                <input
                    type="number"
                    step="0.1"
                    bind:value={scrapingConfig.request_delay}
                    class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
                <p class="text-xs text-gray-500 mt-2 italic">
                    {$language === "de"
                        ? "Wartezeit zwischen Abfragen. Schont die Server und vermeidet Blockierungen."
                        : "Wait time between requests. Keeps the scraper polite and avoids getting blocked."}
                </p>
            </div>
            <div class="space-y-1">
                <label class="block text-sm font-semibold text-gray-700"
                    >{$t("max_targets_per_run")}</label
                >
                <input
                    type="number"
                    min="0"
                    bind:value={scrapingConfig.max_targets_per_run}
                    class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
                <p class="text-xs text-gray-500 mt-2 italic">
                    {$language === "de"
                        ? "Maximale Anzahl Ziele pro Scrape-Durchlauf. 0 = unbegrenzt. Verhindert übermäßigen Ressourcenverbrauch."
                        : "Maximum targets per scrape run. 0 = unlimited. Prevents excessive resource usage."}
                </p>
            </div>
        </div>

        <button
            on:click={saveScrapingConfig}
            disabled={isLoading}
            class="mt-6 btn btn-primary px-8"
        >
            {$t("save_limits")}
        </button>
    </section>

    <!-- ═══════════════════════════════════════════ Scraping Engine ══ -->
    <section class="mb-8 border-b pb-8">
        <h3 class="text-xl font-semibold mb-4 flex items-center">
            <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-6 w-6 mr-2 text-purple-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
            >
                <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18"
                />
            </svg>
            {$language === "de" ? "Scraping-Engine" : "Scraping Engine"}
        </h3>

        <p class="text-sm text-gray-500 mb-5">
            {$language === "de"
                ? "Wähle die Engine für das Web-Crawling. requests+BeautifulSoup ist schnell und ohne weitere Installation nutzbar. Crawl4AI nutzt Headless Chromium und unterstützt JavaScript-gerenderte Seiten."
                : "Choose the crawling engine. requests+BeautifulSoup is fast and works out-of-the-box. Crawl4AI uses a headless browser and supports JavaScript-rendered pages."}
        </p>

        <div class="flex flex-col sm:flex-row gap-4 mb-6">
            <label
                class="flex-1 flex items-start gap-3 p-4 rounded-xl border-2 cursor-pointer transition-colors {scrapingConfig.scraper_engine === 'requests' ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 hover:border-gray-300'}"
            >
                <input
                    type="radio"
                    bind:group={scrapingConfig.scraper_engine}
                    value="requests"
                    class="radio radio-primary mt-0.5"
                />
                <div>
                    <p class="font-semibold text-gray-800">
                        requests + BeautifulSoup
                        <span class="ml-2 badge badge-outline badge-sm">Standard</span>
                    </p>
                    <p class="text-xs text-gray-500 mt-1">
                        {$language === "de"
                            ? "Klassisches HTTP-Scraping. Kein Browser, sehr schnell, keine Zusatz-Installation nötig."
                            : "Classic HTTP scraping. No browser, very fast, no extra setup needed."}
                    </p>
                </div>
            </label>

            <label
                class="flex-1 flex items-start gap-3 p-4 rounded-xl border-2 cursor-pointer transition-colors {scrapingConfig.scraper_engine === 'crawl4ai' ? 'border-purple-500 bg-purple-50' : 'border-gray-200 hover:border-gray-300'}"
            >
                <input
                    type="radio"
                    bind:group={scrapingConfig.scraper_engine}
                    value="crawl4ai"
                    class="radio radio-secondary mt-0.5"
                />
                <div>
                    <p class="font-semibold text-gray-800">
                        Crawl4AI
                        <span class="ml-2 badge badge-secondary badge-sm">JS-Support</span>
                    </p>
                    <p class="text-xs text-gray-500 mt-1">
                        {$language === "de"
                            ? "Headless Chromium. Rendert JavaScript, umgeht einfache Anti-Bot-Maßnahmen. Benötigt crawl4ai + Browser-Installation."
                            : "Headless Chromium. Renders JavaScript, bypasses basic anti-bot measures. Requires crawl4ai + browser installation."}
                    </p>
                </div>
            </label>
        </div>

        {#if scrapingConfig.scraper_engine === "crawl4ai"}
            <div class="space-y-5 p-5 bg-purple-50 rounded-xl border border-purple-100">
                <h4 class="font-semibold text-purple-900 text-sm uppercase tracking-wide">
                    {$language === "de" ? "Crawl4AI Einstellungen" : "Crawl4AI Settings"}
                </h4>

                <!-- External server URL -->
                <div>
                    <label class="block text-sm font-semibold text-gray-700 mb-1">
                        {$language === "de"
                            ? "Externer Crawl4AI-Server (optional)"
                            : "External Crawl4AI Server URL (optional)"}
                    </label>
                    <div class="flex gap-2 items-center max-w-lg">
                        <input
                            type="text"
                            bind:value={scrapingConfig.crawl4ai_server_url}
                            placeholder="http://192.168.1.100:11235"
                            class="input input-bordered flex-1 font-mono"
                        />
                        <button
                            type="button"
                            class="btn btn-outline btn-sm whitespace-nowrap {crawl4aiTesting ? 'loading' : ''}"
                            on:click={testCrawl4aiConnection}
                            disabled={crawl4aiTesting}
                        >
                            {#if !crawl4aiTesting}
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                                </svg>
                            {/if}
                            {$language === "de" ? "Testen" : "Test"}
                        </button>
                    </div>

                    <!-- Test result -->
                    {#if crawl4aiTestResult !== null}
                        <div class="mt-3 p-3 rounded-lg border text-sm {crawl4aiTestResult.ok ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}">
                            <div class="flex items-center gap-2 font-semibold {crawl4aiTestResult.ok ? 'text-green-700' : 'text-red-700'}">
                                {#if crawl4aiTestResult.ok}
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
                                    </svg>
                                {:else}
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                                    </svg>
                                {/if}
                                {crawl4aiTestResult.message}
                            </div>
                            {#if crawl4aiTestResult.ok && crawl4aiTestResult.latency_ms}
                                <p class="text-xs text-green-600 mt-1">Latenz: {crawl4aiTestResult.latency_ms} ms</p>
                            {/if}
                            {#if !crawl4aiTestResult.ok && crawl4aiTestResult.detail}
                                <details class="mt-2">
                                    <summary class="cursor-pointer text-xs text-red-500 font-mono hover:underline">Debug-Info anzeigen</summary>
                                    <pre class="mt-2 text-xs bg-red-100 rounded p-2 overflow-auto whitespace-pre-wrap break-all">{crawl4aiTestResult.detail}</pre>
                                </details>
                            {/if}
                            {#if crawl4aiTestResult.ok && crawl4aiTestResult.response}
                                <details class="mt-2">
                                    <summary class="cursor-pointer text-xs text-green-600 font-mono hover:underline">Server-Antwort</summary>
                                    <pre class="mt-2 text-xs bg-green-100 rounded p-2 overflow-auto">{JSON.stringify(crawl4aiTestResult.response, null, 2)}</pre>
                                </details>
                            {/if}
                        </div>
                    {/if}

                    <p class="text-xs text-gray-500 mt-2">
                        {$language === "de"
                            ? "Leer lassen für lokalen Headless-Browser. URL eintragen um einen externen Crawl4AI-Container (z.B. anderer Proxmox CT) per REST-API zu nutzen. Start: docker run -d -p 11235:11235 unclecode/crawl4ai"
                            : "Leave empty for local headless browser. Enter URL to use an external Crawl4AI container (e.g. another Proxmox CT) via REST API. Start: docker run -d -p 11235:11235 unclecode/crawl4ai"}
                    </p>
                </div>

                <!-- Fallback toggle -->
                <label class="flex items-start gap-3 cursor-pointer">
                    <input
                        type="checkbox"
                        bind:checked={scrapingConfig.crawl4ai_fallback}
                        class="checkbox checkbox-warning mt-0.5"
                    />
                    <span class="text-sm text-gray-700">
                        <span class="font-semibold">
                            {$language === "de"
                                ? "Fallback auf requests bei Fehler"
                                : "Fall back to requests engine on failure"}
                        </span>
                        <br />
                        <span class="text-xs text-gray-500">
                            {$language === "de"
                                ? "Wenn Crawl4AI nicht verfügbar ist (nicht installiert, Server nicht erreichbar, Browser-Absturz), wird automatisch auf requests+BeautifulSoup umgeschaltet."
                                : "If Crawl4AI is unavailable (not installed, server unreachable, browser crash), automatically retries with the requests+BeautifulSoup engine."}
                        </span>
                    </span>
                </label>
            </div>
        {/if}

        <button
            on:click={saveScrapingConfig}
            disabled={isLoading}
            class="mt-6 btn btn-primary px-8"
        >
            {$language === "de" ? "Engine-Einstellungen speichern" : "Save Engine Settings"}
        </button>
    </section>

    <!-- ═══════════════════════════════════════════ KI-Analyse ══ -->
    <section class="mb-8 border-b pb-8">
        <h3 class="text-xl font-semibold mb-4 flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 mr-2 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            {$t("ai_config")}
        </h3>

        <p class="text-sm text-gray-500 mb-5">
            {$language === "de"
                ? "Konfiguriere einen KI-Anbieter (OpenRouter, OpenAI, Anthropic oder Custom), um Scraping-Ergebnisse automatisch analysieren und zusammenfassen zu lassen."
                : "Configure an AI provider (OpenRouter, OpenAI, Anthropic or Custom) to automatically analyze and summarize scraping results."}
        </p>

        {#if aiConfigLoaded}
            <div class="space-y-5">
                <!-- Enable toggle -->
                <label class="flex items-center gap-3 cursor-pointer">
                    <input type="checkbox" bind:checked={aiConfig.enabled} class="checkbox checkbox-primary" />
                    <span class="font-semibold text-gray-800">{$t("ai_enabled")}</span>
                </label>

                <!-- Provider -->
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                    {#each ["openrouter", "openai", "anthropic", "custom"] as p}
                        <label class="flex items-center gap-2 p-3 rounded-xl border-2 cursor-pointer transition-colors {aiConfig.provider === p ? 'border-emerald-500 bg-emerald-50' : 'border-gray-200 hover:border-gray-300'}">
                            <input type="radio" bind:group={aiConfig.provider} value={p} class="radio radio-primary radio-sm" />
                            <span class="font-medium text-sm capitalize">{p}</span>
                        </label>
                    {/each}
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <!-- API Key -->
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-1">{$t("ai_api_key")}</label>
                        <input type="password" bind:value={aiConfig.api_key} placeholder="sk-..." class="input input-bordered w-full font-mono" autocomplete="off" />
                    </div>
                    <!-- Model -->
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-1">{$t("ai_model")}</label>
                        <input type="text" bind:value={aiConfig.model_name} placeholder="openai/gpt-4o-mini" class="input input-bordered w-full font-mono" />
                        <p class="text-xs text-gray-400 mt-1">{$language === "de" ? "OpenRouter: z.B. openai/gpt-4o-mini, anthropic/claude-3-haiku" : "OpenRouter: e.g. openai/gpt-4o-mini, anthropic/claude-3-haiku"}</p>
                    </div>
                </div>

                {#if aiConfig.provider === "custom"}
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-1">{$t("ai_base_url")}</label>
                        <input type="text" bind:value={aiConfig.base_url} placeholder="https://my-api.example.com/v1" class="input input-bordered w-full font-mono" />
                    </div>
                {/if}

                <!-- System prompt -->
                <div>
                    <label class="block text-sm font-semibold text-gray-700 mb-1">{$t("ai_system_prompt")}</label>
                    <textarea
                        bind:value={aiConfig.system_prompt}
                        rows="4"
                        placeholder={$language === "de" ? "Leer lassen für Standard-Prompt (Bauland/Gemeinde-Fokus)" : "Leave empty for default prompt (Bauland/municipality focus)"}
                        class="textarea textarea-bordered w-full font-mono text-sm"
                    ></textarea>
                </div>

                <button on:click={saveAiConfig} disabled={isLoading} class="btn btn-primary px-8">
                    {$t("ai_save_config")}
                </button>
            </div>
        {:else}
            <div class="flex justify-center p-8">
                <span class="loading loading-spinner text-emerald-600"></span>
            </div>
        {/if}
    </section>

    <section>
        <h3 class="text-xl font-semibold mb-4 flex items-center">
            <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-6 w-6 mr-2 text-green-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
            >
                <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                />
            </svg>
            {$t("notification_channels")}
        </h3>
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div class="space-y-4">
                <h4
                    class="font-medium text-gray-600 uppercase text-xs tracking-widest border-b pb-2"
                >
                    Active Channels
                </h4>
                {#if notificationConfigs.length === 0}
                    <p class="text-gray-400 italic text-sm">
                        No notification channels configured yet.
                    </p>
                {/if}
                {#each notificationConfigs as config}
                    <div
                        class="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-100 hover:border-gray-200 transition-colors"
                    >
                        <div class="flex items-center">
                            <span
                                class="badge badge-outline badge-sm mr-3 uppercase font-mono"
                                >{config.type}</span
                            >
                            <span
                                class="text-gray-700 truncate max-w-[200px]"
                                title={config.recipient}
                                >{config.recipient}</span
                            >
                            {#if !config.enabled}
                                <span class="ml-2 badge badge-error badge-xs"
                                    >{$t("disabled")}</span
                                >
                            {/if}
                        </div>
                        <div class="flex gap-2">
                            <button
                                on:click={() => testNotification(config.id)}
                                disabled={isLoading}
                                class="btn btn-ghost btn-xs text-indigo-600 hover:bg-indigo-50 transition-colors"
                                >{$t("test")}</button
                            >
                            <button
                                on:click={() => deleteNotification(config.id)}
                                class="btn btn-ghost btn-xs text-red-500 hover:bg-red-50 transition-colors"
                                >{$t("delete")}</button
                            >
                        </div>
                    </div>
                {/each}
            </div>

            <div
                class="bg-gray-50 p-6 rounded-xl border-2 border-dashed border-gray-200"
            >
                <h4 class="font-bold mb-4 text-gray-800">
                    {$t("add_new_channel")}
                </h4>
                <div class="space-y-4">
                    <div class="form-control">
                        <label class="label"
                            ><span class="label-text">Type</span></label
                        >
                        <select
                            bind:value={newNotification.type}
                            class="select select-bordered w-full"
                        >
                            <option value="webhook">{$t("webhook")}</option>
                            <option value="email">{$t("email")}</option>
                        </select>
                    </div>
                    <div class="form-control">
                        <label class="label"
                            ><span class="label-text">{$t("recipient")}</span
                            ></label
                        >
                        <input
                            type="text"
                            bind:value={newNotification.recipient}
                            placeholder={newNotification.type === "email"
                                ? "your@email.com"
                                : "https://webhook.site/..."}
                            class="input input-bordered w-full"
                        />
                    </div>
                    <button
                        on:click={addNotification}
                        disabled={isLoading}
                        class="btn btn-success btn-block"
                    >
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            class="h-5 w-5 mr-2"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                        >
                            <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                stroke-width="2"
                                d="M12 4v16m8-8H4"
                            />
                        </svg>
                        {$t("add")}
                    </button>
                </div>
            </div>
        </div>
    </section>
</div>
