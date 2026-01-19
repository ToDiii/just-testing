<script lang="ts">
  import TargetManager from "./lib/components/TargetManager.svelte";
  import Dashboard from "./lib/components/Dashboard.svelte";
  import AdminDashboard from "./lib/components/AdminDashboard.svelte";
  import { onMount } from "svelte";
  import { api } from "./lib/api";
  import { buildInfo } from "virtual:build-info";
  import { language, t } from "./lib/stores";
  import "./app.css";

  let currentView: "dashboard" | "targets" | "admin" = "dashboard";

  // ... (scrapeStatus logic remains same) ...
  let allTargets: any[] = [];
  let displayedTargets: any[] = [];
  let mapCenter: [number, number] | null = null;

  type ScrapeStatus = {
    scrape_status: "idle" | "running";
  };
  let scrapeStatus: ScrapeStatus = { scrape_status: "idle" };

  async function fetchScrapeStatus() {
    try {
      scrapeStatus = await api("/api/scrape/status");
    } catch (error) {
      console.error("Failed to fetch scrape status:", error);
    }
  }

  function handleSearchComplete(event: any) {
    const { targets: foundTargets, center } = event.detail;
    displayedTargets = foundTargets;
    if (center) {
      mapCenter = [center.lat, center.lon];
    }
  }

  function resetView() {
    displayedTargets = allTargets;
  }

  onMount(() => {
    async function init() {
      try {
        allTargets = await api("/api/targets?limit=10000");
        displayedTargets = allTargets;
      } catch (error) {
        console.error("Failed to fetch targets for map:", error);
      }
    }

    init();
    fetchScrapeStatus();
    const interval = setInterval(fetchScrapeStatus, 5000);
    return () => clearInterval(interval);
  });
</script>

<main class="bg-gray-100 min-h-screen font-sans">
  <header class="bg-white shadow">
    <div class="container mx-auto px-4 py-6">
      <div class="flex justify-between items-center">
        <h1 class="text-3xl font-bold text-gray-800">{$t("app_title")}</h1>
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2 bg-gray-100 p-1 rounded-lg">
            <button
              class="px-2 py-1 rounded text-xs font-bold transition-colors {$language ===
              'de'
                ? 'bg-white shadow text-blue-600'
                : 'text-gray-500 hover:text-gray-800'}"
              on:click={() => ($language = "de")}
            >
              DE
            </button>
            <button
              class="px-2 py-1 rounded text-xs font-bold transition-colors {$language ===
              'en'
                ? 'bg-white shadow text-blue-600'
                : 'text-gray-500 hover:text-gray-800'}"
              on:click={() => ($language = "en")}
            >
              EN
            </button>
          </div>
          {#if scrapeStatus.scrape_status === "running"}
            <div class="flex items-center text-sm text-blue-600 font-medium">
              <span class="loading loading-spinner loading-sm mr-2"></span>
              {$t("scraping_in_progress")}
            </div>
          {/if}
        </div>
      </div>
      <nav class="mt-4">
        <button
          class="px-4 py-2 rounded-md mr-2 {currentView === 'dashboard'
            ? 'bg-blue-500 text-white shadow-md'
            : 'bg-gray-200 hover:bg-gray-300 transition-colors'}"
          on:click={() => (currentView = "dashboard")}
        >
          {$t("dashboard")}
        </button>
        <button
          class="px-4 py-2 rounded-md mr-2 {currentView === 'targets'
            ? 'bg-blue-500 text-white shadow-md'
            : 'bg-gray-200 hover:bg-gray-300 transition-colors'}"
          on:click={() => (currentView = "targets")}
        >
          {$t("manage_targets")}
        </button>
        <button
          class="px-4 py-2 rounded-md {currentView === 'admin'
            ? 'bg-blue-500 text-white shadow-md'
            : 'bg-gray-200 hover:bg-gray-300 transition-colors'}"
          on:click={() => (currentView = "admin")}
        >
          {$t("admin")}
        </button>
      </nav>
    </div>
  </header>

  <div class="container mx-auto p-4 mt-6">
    {#if currentView === "dashboard"}
      <Dashboard />
    {:else if currentView === "admin"}
      <AdminDashboard />
    {:else}
      <TargetManager />
    {/if}
  </div>

  <div
    class="fixed bottom-2 right-2 bg-gray-800 text-white text-xs p-2 rounded shadow-lg z-50"
  >
    Build: {buildInfo.buildDate}
  </div>
</main>
