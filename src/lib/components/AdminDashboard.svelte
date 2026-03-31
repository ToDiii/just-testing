<script lang="ts">
    import { onMount } from "svelte";
    import { api } from "../api";
    import { t, language } from "../stores";

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
    };

    let notificationConfigs: NotificationConfig[] = [];
    let newNotification = {
        type: "webhook",
        recipient: "",
        enabled: true,
    };

    let isLoading = false;
    let message = "";

    onMount(async () => {
        await loadConfigs();
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

    async function saveScrapingConfig() {
        isLoading = true;
        message = "";
        try {
            await api("/api/config/scraping", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(scrapingConfig),
            });
            message = "Scraping configuration saved!";
        } catch (error: any) {
            message = "Error saving scraping config: " + error.message;
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
        } catch (error: any) {
            message = "Error adding notification: " + error.message;
        } finally {
            isLoading = false;
        }
    }

    async function deleteNotification(id: number) {
        isLoading = true;
        try {
            await api(`/api/notifications/config/${id}`, {
                method: "DELETE",
            });
            await loadConfigs();
        } catch (error: any) {
            message = "Error deleting notification: " + error.message;
        } finally {
            isLoading = false;
        }
    }

    async function testNotification(id: number) {
        isLoading = true;
        message = "";
        try {
            const result = await api(`/api/notifications/test/${id}`, {
                method: "POST",
            });
            message = result.message || "Test notification sent!";
        } catch (error: any) {
            message = "Error testing notification: " + error.message;
        } finally {
            isLoading = false;
        }
    }
</script>

<div class="p-6 bg-white rounded-lg shadow-md">
    <h2 class="text-2xl font-bold mb-6">{$t("admin_dashboard")}</h2>

    {#if message}
        <div
            class="p-4 mb-4 text-sm text-blue-700 bg-blue-100 rounded-lg"
            role="alert"
        >
            {message}
        </div>
    {/if}

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
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
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
        </div>

        <!-- Scraper Engine Selector -->
        <div class="mt-6 p-4 bg-indigo-50 rounded-xl border border-indigo-100">
            <h4 class="font-semibold text-gray-800 mb-1">
                {$language === "de" ? "Scraping-Engine" : "Scraping Engine"}
            </h4>
            <p class="text-xs text-gray-500 mb-3 italic">
                {$language === "de"
                    ? "Wähle die Engine für das Web-Crawling. Crawl4AI nutzt einen echten Browser (Headless Chromium) und unterstützt JavaScript-gerenderte Seiten."
                    : "Choose the crawling engine. Crawl4AI uses a real headless browser and supports JavaScript-rendered pages — useful for modern municipality sites."}
            </p>
            <div class="flex gap-4 mb-4">
                <label class="flex items-center gap-2 cursor-pointer">
                    <input
                        type="radio"
                        bind:group={scrapingConfig.scraper_engine}
                        value="requests"
                        class="radio radio-primary radio-sm"
                    />
                    <span class="text-sm font-medium text-gray-700">
                        requests + BeautifulSoup
                        <span class="ml-1 badge badge-outline badge-xs">Standard</span>
                    </span>
                </label>
                <label class="flex items-center gap-2 cursor-pointer">
                    <input
                        type="radio"
                        bind:group={scrapingConfig.scraper_engine}
                        value="crawl4ai"
                        class="radio radio-secondary radio-sm"
                    />
                    <span class="text-sm font-medium text-gray-700">
                        Crawl4AI
                        <span class="ml-1 badge badge-secondary badge-xs">JS-Support</span>
                    </span>
                </label>
            </div>

            {#if scrapingConfig.scraper_engine === "crawl4ai"}
                <div class="mt-2 space-y-4 border-t border-indigo-200 pt-4">
                    <!-- External server URL -->
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-1">
                            {$language === "de"
                                ? "Externer Crawl4AI-Server (optional)"
                                : "External Crawl4AI Server URL (optional)"}
                        </label>
                        <input
                            type="text"
                            bind:value={scrapingConfig.crawl4ai_server_url}
                            placeholder="http://192.168.1.100:11235"
                            class="input input-bordered input-sm w-full max-w-md font-mono"
                        />
                        <p class="text-xs text-gray-500 mt-1 italic">
                            {$language === "de"
                                ? "Leer lassen = lokaler Headless-Browser. Befüllen = REST-API eines anderen Crawl4AI-Containers (z.B. Proxmox CT)."
                                : "Leave empty to use a local headless browser. Fill in to use a remote Crawl4AI container (e.g. another Proxmox CT) via its REST API."}
                        </p>
                    </div>

                    <!-- Fallback toggle -->
                    <label class="flex items-start gap-3 cursor-pointer">
                        <input
                            type="checkbox"
                            bind:checked={scrapingConfig.crawl4ai_fallback}
                            class="checkbox checkbox-warning checkbox-sm mt-0.5"
                        />
                        <span class="text-sm text-gray-700">
                            <span class="font-semibold">
                                {$language === "de"
                                    ? "Fallback auf requests bei Fehler"
                                    : "Fall back to requests engine on failure"}
                            </span>
                            <br />
                            <span class="text-xs text-gray-500 italic">
                                {$language === "de"
                                    ? "Wenn Crawl4AI nicht erreichbar ist oder abstürzt, wird automatisch auf den normalen Scraper umgeschaltet."
                                    : "If Crawl4AI is unreachable or crashes, the scraper automatically retries with the requests engine."}
                            </span>
                        </span>
                    </label>
                </div>
            {/if}
        </div>

        <button
            on:click={saveScrapingConfig}
            disabled={isLoading}
            class="mt-6 btn btn-primary px-8"
        >
            {$t("save_limits")}
        </button>
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
