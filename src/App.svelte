<script lang="ts">
  import TargetManager from "./lib/components/TargetManager.svelte";
  import ResultsViewer from "./lib/components/ResultsViewer.svelte";
  import Map from "./lib/components/Map.svelte";
  import RadiusSearch from "./lib/components/RadiusSearch.svelte";
  import { onMount } from "svelte";
  import { api } from "./lib/api";
  import { buildInfo } from "virtual:build-info";
  import "./app.css";

  let currentView: "map" | "targets" | "results" = "map";
  let allTargets: any[] = [];
  let displayedTargets: any[] = [];

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
    const { targets: foundTargets } = event.detail;
    displayedTargets = foundTargets;
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
        <h1 class="text-3xl font-bold text-gray-800">Scraper Dashboard</h1>
        {#if scrapeStatus.scrape_status === "running"}
          <div class="flex items-center text-sm text-gray-500">
            <span class="loading loading-spinner loading-sm mr-2"></span>
            Scraping in progress...
          </div>
        {/if}
      </div>
      <nav class="mt-4">
        <button
          class="px-4 py-2 rounded-md mr-2 {currentView === 'map'
            ? 'bg-blue-500 text-white'
            : 'bg-gray-200'}"
          on:click={() => (currentView = "map")}
        >
          Map
        </button>
        <button
          class="px-4 py-2 rounded-md mr-2 {currentView === 'results'
            ? 'bg-blue-500 text-white'
            : 'bg-gray-200'}"
          on:click={() => (currentView = "results")}
        >
          Results
        </button>
        <button
          class="px-4 py-2 rounded-md {currentView === 'targets'
            ? 'bg-blue-500 text-white'
            : 'bg-gray-200'}"
          on:click={() => (currentView = "targets")}
        >
          Manage Targets
        </button>
      </nav>
    </div>
  </header>

  <div class="container mx-auto p-4 mt-6">
    {#if currentView === "map"}
      <div class="w-full h-[70vh] mb-4 relative">
        <Map targets={displayedTargets} />
      </div>
      <RadiusSearch on:searchcomplete={handleSearchComplete} />
      <button class="btn btn-sm btn-secondary mt-2" on:click={resetView}
        >Reset View</button
      >
    {:else if currentView === "results"}
      <ResultsViewer />
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
