<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { api } from "../api";
  import { uiState, t } from "../stores";

  export let forcedTargetIds: number[] | null = null;

  $: if (forcedTargetIds) {
    fetchResults();
  }

  type ViewMode = "table" | "cards-small" | "cards-large";
  let viewMode: ViewMode = (typeof localStorage !== "undefined"
    ? (localStorage.getItem("resultsViewMode") as ViewMode) || "table"
    : "table");

  function setViewMode(mode: ViewMode) {
    viewMode = mode;
    localStorage.setItem("resultsViewMode", mode);
  }

  // ... types ...

  type ScrapeResult = {
    id: number;
    title: string;
    description: string;
    url: string;
    source: string;
    publication_date: string;
    scraped_at: string;
  };

  type Region = {
    id: number;
    name: string;
    type: string;
  };

  type Target = {
    id: number;
    name: string;
    url: string;
  };

  let results: ScrapeResult[] = [];
  let regions: Region[] = [];
  let targets: Target[] = [];
  let isLoading = true;
  let errorMessage = "";
  let logPollingInterval: any = null;
  let logContainer: HTMLElement;

  // Advanced Filtering State
  type TextOperator = "contains" | "equals" | "starts_with" | "ends_with";
  type DateOperator = "after" | "before" | "equals" | "all";

  let columnFilters = {
    title: { value: "", operator: "contains" as TextOperator },
    source: { value: "", operator: "equals" as TextOperator },
    publication_date: { value: "", operator: "all" as DateOperator },
    scraped_at: { value: "", operator: "all" as DateOperator },
  };

  const textOperators: TextOperator[] = [
    "contains",
    "equals",
    "starts_with",
    "ends_with",
  ];
  const dateOperators: DateOperator[] = ["all", "after", "before", "equals"];

  let showFilterRow = true;
  let selectedIds = new Set<number>();

  $: filteredResults = results.filter((item) => {
    // Title Filter
    if (columnFilters.title.value) {
      const val = columnFilters.title.value.toLowerCase();
      const title = item.title.toLowerCase();
      const op = columnFilters.title.operator;
      if (op === "contains" && !title.includes(val)) return false;
      if (op === "equals" && title !== val) return false;
      if (op === "starts_with" && !title.startsWith(val)) return false;
      if (op === "ends_with" && !title.endsWith(val)) return false;
    }

    // Source Filter
    if (columnFilters.source.value) {
      if (item.source !== columnFilters.source.value) return false;
    }

    // Publication Date Filter
    if (
      columnFilters.publication_date.operator !== "all" &&
      columnFilters.publication_date.value
    ) {
      const filterDate = new Date(columnFilters.publication_date.value);
      const itemDate = new Date(item.publication_date);
      const op = columnFilters.publication_date.operator;
      if (op === "after" && itemDate <= filterDate) return false;
      if (op === "before" && itemDate >= filterDate) return false;
      if (
        op === "equals" &&
        itemDate.toDateString() !== filterDate.toDateString()
      )
        return false;
    }

    // Scraped At Filter
    if (
      columnFilters.scraped_at.operator !== "all" &&
      columnFilters.scraped_at.value
    ) {
      const filterDate = new Date(columnFilters.scraped_at.value);
      const itemDate = new Date(item.scraped_at);
      const op = columnFilters.scraped_at.operator;
      if (op === "after" && itemDate <= filterDate) return false;
      if (op === "before" && itemDate >= filterDate) return false;
      if (
        op === "equals" &&
        itemDate.toDateString() !== filterDate.toDateString()
      )
        return false;
    }

    return true;
  });

  function toggleSelectAll(e: Event) {
    const checked = (e.target as HTMLInputElement).checked;
    if (checked) {
      selectedIds = new Set(filteredResults.map((r) => r.id));
    } else {
      selectedIds = new Set();
    }
  }

  function toggleSelect(id: number) {
    if (selectedIds.has(id)) {
      selectedIds.delete(id);
    } else {
      selectedIds.add(id);
    }
    selectedIds = selectedIds; // trigger reactivity
  }

  async function deleteSelected() {
    if (selectedIds.size === 0) return;
    if (
      !confirm(
        `Möchten Sie ${selectedIds.size} Einträge wirklich löschen (ignorieren)?`,
      )
    )
      return;

    try {
      await api("/api/results/bulk-ignore", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(Array.from(selectedIds)),
      });
      selectedIds = new Set();
      fetchResults(); // Refresh list
    } catch (error) {
      errorMessage = (error as Error).message;
    }
  }

  // AI Analysis
  let showAiModal = false;
  let aiModalTab: "current" | "history" = "current";
  let aiAnalysisLoading = false;
  let aiAnalysisResult = "";
  let aiAnalysisError = "";
  let aiHistory: { id: number; created_at: string; result_text: string; result_count: number; mode: string }[] = [];
  let aiHistoryLoading = false;
  let analyzedResultIds = new Set<number>(); // result IDs that have been analyzed

  async function fetchAiHistory() {
    aiHistoryLoading = true;
    try {
      const analyses = await api("/api/ai/analyses?limit=20");
      aiHistory = analyses;
      // Collect all result IDs that appear in any analysis
      const newAnalyzed = new Set<number>();
      for (const a of analyses) {
        try {
          // target_ids_json stores the result_ids array
          if (a.target_ids_json) {
            const ids: number[] = JSON.parse(a.target_ids_json);
            ids.forEach((id) => newAnalyzed.add(id));
          }
        } catch {}
      }
      analyzedResultIds = newAnalyzed;
    } catch (error) {
      console.error("Failed to fetch AI history:", error);
    } finally {
      aiHistoryLoading = false;
    }
  }

  async function runAiAnalysis() {
    aiAnalysisLoading = true;
    aiAnalysisResult = "";
    aiAnalysisError = "";
    aiModalTab = "current";
    showAiModal = true;
    const ids = Array.from(selectedIds);
    try {
      const res = await api("/api/ai/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ result_ids: ids, mode: "summary" }),
      });
      aiAnalysisResult = res.result_text || "";
      // Mark these IDs as analyzed and refresh history
      ids.forEach((id) => analyzedResultIds.add(id));
      analyzedResultIds = analyzedResultIds; // trigger reactivity
      fetchAiHistory();
    } catch (error) {
      aiAnalysisError = (error as Error).message;
    } finally {
      aiAnalysisLoading = false;
    }
  }

  $: uniqueSources = [...new Set(results.map((r) => r.source))].sort();

  let userHasScrolledUp = false;

  function handleLogScroll(e: Event) {
    const target = e.target as HTMLElement;
    // Check if user is near bottom (within 20px)
    const isAtBottom =
      target.scrollHeight - target.scrollTop <= target.clientHeight + 20;
    userHasScrolledUp = !isAtBottom;
  }

  $: if ($uiState.logs && logContainer && !userHasScrolledUp) {
    setTimeout(() => {
      if (logContainer) logContainer.scrollTop = logContainer.scrollHeight;
    }, 50);
  }

  async function fetchResults() {
    isLoading = true;
    errorMessage = "";
    const params = new URLSearchParams();
    if ($uiState.filterSearch) params.append("search", $uiState.filterSearch);

    if (forcedTargetIds && forcedTargetIds.length > 0) {
      params.append("target_ids", forcedTargetIds.join(","));
    } else {
      if ($uiState.filterRegionId)
        params.append("region_id", $uiState.filterRegionId.toString());
      if ($uiState.selectedScrapeTargetId)
        params.append("target_id", $uiState.selectedScrapeTargetId.toString());
    }

    try {
      results = await api(`/api/results?${params.toString()}`);
    } catch (error) {
      errorMessage = (error as Error).message;
    } finally {
      isLoading = false;
    }
  }

  async function fetchStatus() {
    try {
      const status = await api("/api/scrape/status");
      $uiState.isScraping = status.scrape_status === "running";
      if ($uiState.isScraping && !logPollingInterval) {
        startPolling();
      } else if (!$uiState.isScraping && logPollingInterval) {
        // Stop polling after a small delay to get final logs
        setTimeout(stopPolling, 3000);
      }
    } catch (error) {
      console.error("Failed to fetch status:", error);
    }
  }

  async function fetchLogs() {
    try {
      const newLogs = await api("/api/scrape/logs");
      $uiState.logs = newLogs;
    } catch (error) {
      console.error("Failed to fetch logs:", error);
    }
  }

  async function fetchRegions() {
    try {
      regions = await api("/api/regions");
    } catch (error) {
      console.error("Failed to fetch regions:", error);
    }
  }

  async function fetchTargets() {
    try {
      targets = await api("/api/targets");
    } catch (error) {
      console.error("Failed to fetch targets:", error);
    }
  }

  function startPolling() {
    if (logPollingInterval) return;
    $uiState.showLogs = true;
    logPollingInterval = setInterval(fetchLogs, 1000);
  }

  function stopPolling() {
    if (logPollingInterval) {
      clearInterval(logPollingInterval);
      logPollingInterval = null;
    }
  }

  async function runScrape() {
    $uiState.isScraping = true;
    errorMessage = "";
    $uiState.showLogs = true;
    $uiState.logs = [];

    startPolling();

    try {
      const params = new URLSearchParams();
      if ($uiState.selectedScrapeTargetId) {
        params.append("target_id", $uiState.selectedScrapeTargetId.toString());
      } else if ($uiState.selectedScrapeRegionId) {
        params.append("region_id", $uiState.selectedScrapeRegionId.toString());
      }

      const url = `/api/scrape?${params.toString()}`;
      await api(url, { method: "POST" });
    } catch (error) {
      errorMessage = (error as Error).message;
      $uiState.isScraping = false;
      stopPolling();
    }
  }
  async function stopScrape() {
    try {
      await api("/api/scrape/stop", { method: "POST" });
    } catch (error) {
      errorMessage = (error as Error).message;
    }
  }

  onMount(() => {
    fetchResults();
    fetchRegions();
    fetchTargets();
    fetchStatus();
    fetchAiHistory();

    // Check status periodically
    const statusInterval = setInterval(fetchStatus, 3000);

    return () => {
      clearInterval(statusInterval);
      stopPolling();
    };
  });
</script>

<div class="bg-white p-6 rounded-lg shadow-md">
  <!-- Scrape Control Center -->
  <div
    class="bg-gradient-to-r from-indigo-600 to-purple-600 p-8 rounded-t-lg -mx-6 -mt-6 mb-8 text-white shadow-lg"
  >
    <div class="flex flex-col xl:flex-row justify-between items-center gap-6">
      <div class="text-center xl:text-left">
        <h2 class="text-3xl font-extrabold tracking-tight">
          {$t("scrape_control_center")}
        </h2>
        <p class="mt-1 text-indigo-100 italic">{$t("launch_targeted_scans")}</p>
      </div>

      <div
        class="flex flex-col lg:flex-row items-center gap-4 w-full xl:w-auto"
      >
        <div class="flex flex-col sm:flex-row gap-3 w-full lg:w-auto">
          <!-- Region Selector -->
          <div class="relative group flex-1 sm:w-48">
            <select
              bind:value={$uiState.selectedScrapeRegionId}
              on:change={() => {
                if ($uiState.selectedScrapeRegionId)
                  $uiState.selectedScrapeTargetId = null;
              }}
              class="select select-bordered bg-white/10 text-white border-white/20 focus:bg-white focus:text-gray-900 transition-all w-full"
              disabled={$uiState.isScraping}
            >
              <option value={null} class="text-gray-900"
                >{$t("all_regions")}</option
              >
              {#each regions as region (region.id)}
                <option value={region.id} class="text-gray-900"
                  >{region.name}</option
                >
              {/each}
            </select>
            <div
              class="absolute -top-6 left-1 text-xs font-bold uppercase tracking-wider text-indigo-200"
            >
              {$t("region")}
            </div>
          </div>

          <!-- Target Selector -->
          <div class="relative group flex-1 sm:w-56">
            <select
              bind:value={$uiState.selectedScrapeTargetId}
              on:change={() => {
                if ($uiState.selectedScrapeTargetId)
                  $uiState.selectedScrapeRegionId = null;
              }}
              class="select select-bordered bg-white/10 text-white border-white/20 focus:bg-white focus:text-gray-900 transition-all w-full"
              disabled={$uiState.isScraping}
            >
              <option value={null} class="text-gray-900"
                >{$t("all_targets")}</option
              >
              {#each targets as target (target.id)}
                <option value={target.id} class="text-gray-900"
                  >{target.name || target.url}</option
                >
              {:else}
                <option disabled value={null}>No targets available</option>
              {/each}
            </select>
            <div
              class="absolute -top-6 left-1 text-xs font-bold uppercase tracking-wider text-indigo-200"
            >
              {$t("municipality")}
            </div>
          </div>
        </div>

        <div class="flex flex-col sm:flex-row gap-3 w-full lg:w-auto">
          <button
            class="btn btn-lg border-none bg-white text-indigo-700 hover:bg-indigo-50 shadow-xl px-12 transition-all transform hover:scale-105 active:scale-95 disabled:bg-indigo-800 disabled:text-indigo-400 w-full lg:w-48"
            on:click={runScrape}
            disabled={$uiState.isScraping}
          >
            {#if $uiState.isScraping}
              <span class="loading loading-spinner text-indigo-400"></span>
              <span class="animate-pulse">{$t("active")}</span>
            {:else}
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-6 w-6 mr-2"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
              {$t("start_scrape")}
            {/if}
          </button>

          {#if $uiState.isScraping}
            <button
              class="btn btn-lg border-none bg-red-500 text-white hover:bg-red-600 shadow-xl px-8 transition-all transform hover:scale-105 active:scale-95 w-full lg:w-48"
              on:click={stopScrape}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-6 w-6 mr-2"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
              {$t("cancel_scrape")}
            </button>
          {/if}
        </div>
      </div>
    </div>
  </div>

  <!-- Filters & Logs Toggle -->
  <div class="mb-4 flex flex-col md:flex-row gap-4 items-center">
    <div class="flex-1 w-full">
      <input
        type="text"
        placeholder={$t("filter_by_keyword")}
        bind:value={$uiState.filterSearch}
        on:input={() => fetchResults()}
        class="input input-bordered w-full"
      />
    </div>
    <div class="w-full md:w-64">
      <select
        bind:value={$uiState.filterRegionId}
        on:change={() => fetchResults()}
        class="select select-bordered w-full"
      >
        <option value={null}>{$t("view_all_regions")}</option>
        {#each regions as region (region.id)}
          <option value={region.id}>{region.name}</option>
        {/each}
      </select>
    </div>
    <button
      on:click={() => ($uiState.showLogs = !$uiState.showLogs)}
      class="btn btn-ghost btn-sm text-indigo-600 font-bold"
    >
      {$uiState.showLogs ? $t("hide_logs") : $t("view_engine_logs")}
    </button>
  </div>

  <!-- Log Viewer -->
  {#if $uiState.showLogs || $uiState.isScraping}
    <div
      class="mb-6 border rounded-lg overflow-hidden bg-gray-900 text-gray-100 shadow-2xl"
    >
      <div
        class="flex justify-between items-center bg-gray-800 px-4 py-2 border-b border-gray-700"
      >
        <h3 class="font-mono text-xs font-bold flex items-center">
          <span
            class="w-2 h-2 rounded-full mr-2 {$uiState.isScraping
              ? 'bg-green-500 animate-ping'
              : 'bg-gray-500'}"
          ></span>
          SCRAPER_LOG_STREAM v1.0
        </h3>
        <button
          on:click={() => ($uiState.logs = [])}
          class="text-[10px] uppercase font-bold text-gray-400 hover:text-white transition-colors"
          >{$t("clear_console")}</button
        >
      </div>
      <div
        bind:this={logContainer}
        on:scroll={handleLogScroll}
        class="p-4 h-64 overflow-y-auto font-mono text-xs space-y-1 custom-scrollbar"
      >
        {#each $uiState.logs as log}
          <div
            class="border-l-2 pl-2 {log.includes('[ERROR]')
              ? 'border-red-500 text-red-400'
              : log.includes('[MATCH]')
                ? 'border-green-500 text-green-400'
                : 'border-gray-700 text-gray-300'}"
          >
            {log}
          </div>
        {:else}
          {#if !$uiState.isScraping}
            <div class="text-gray-600 italic">{$t("no_logs_recorded")}</div>
          {/if}
        {/each}
        {#if $uiState.isScraping}
          <div
            class="animate-pulse text-indigo-400 border-l-2 border-indigo-500 pl-2"
          >
            {$t("engine_active")}
          </div>
        {/if}
      </div>
    </div>
  {/if}

  <!-- Error Message -->
  {#if errorMessage}
    <div class="alert alert-error my-4 shadow-lg">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="stroke-current flex-shrink-0 h-6 w-6"
        fill="none"
        viewBox="0 0 24 24"
        ><path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
        /></svg
      >
      <span>{errorMessage}</span>
    </div>
  {/if}

  <!-- Results Section -->
  <div class="overflow-x-auto w-full">
    {#if isLoading}
      <div class="flex justify-center p-8">
        <span class="loading loading-dots loading-lg text-indigo-600"></span>
        <span class="ml-4 font-bold text-indigo-600"
          >{$t("loading_results")}</span
        >
      </div>
    {:else if results.length === 0}
      <div
        class="bg-gray-50 border-2 border-dashed border-gray-200 rounded-lg p-12 text-center"
      >
        <p class="text-gray-500 font-medium">{$t("no_results_found")}</p>
      </div>
    {:else}
      <!-- Toolbar: select-all, delete, AI, view-mode toggle -->
      <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-3 mb-4">
        <div class="flex items-center gap-4 flex-wrap">
          <label class="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              class="checkbox checkbox-sm checkbox-primary"
              checked={selectedIds.size === filteredResults.length &&
                filteredResults.length > 0}
              on:change={toggleSelectAll}
            />
            <span class="text-sm font-bold text-gray-600"
              >{$t("select_all")} ({filteredResults.length})</span
            >
          </label>

          {#if selectedIds.size > 0}
            <button
              class="btn btn-error btn-sm animate-in fade-in zoom-in duration-200"
              on:click={deleteSelected}
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              Löschen ({selectedIds.size})
            </button>
            <button
              class="btn btn-accent btn-sm animate-in fade-in zoom-in duration-200"
              on:click={runAiAnalysis}
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              {$t("ai_analysis")} ({selectedIds.size})
            </button>
          {/if}
        </div>

        <!-- View mode toggle -->
        <div class="join border border-gray-200 rounded-lg">
          <button
            class="join-item btn btn-sm {viewMode === 'table' ? 'btn-primary' : 'btn-ghost'}"
            title={$t("view_table")}
            on:click={() => setViewMode("table")}
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M3 14h18M3 6h18M3 18h18" />
            </svg>
          </button>
          <button
            class="join-item btn btn-sm {viewMode === 'cards-small' ? 'btn-primary' : 'btn-ghost'}"
            title={$t("view_cards_small")}
            on:click={() => setViewMode("cards-small")}
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
            </svg>
          </button>
          <button
            class="join-item btn btn-sm {viewMode === 'cards-large' ? 'btn-primary' : 'btn-ghost'}"
            title={$t("view_cards_large")}
            on:click={() => setViewMode("cards-large")}
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </button>
        </div>
      </div>

      <!-- TABLE VIEW -->
      {#if viewMode === "table"}
        <table class="table w-full">
          <thead>
            <tr class="bg-gray-100 border-b-2 border-indigo-100">
              <th class="w-12"></th>
              <th class="text-indigo-900 group">
                <div class="flex items-center justify-between">
                  <span>{$t("title")}</span>
                  <button
                    on:click={() => (showFilterRow = !showFilterRow)}
                    class="btn btn-ghost btn-xs opacity-50 group-hover:opacity-100"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                      <path fill-rule="evenodd" d="M3 3a1 1 0 011-1h12a1 1 0 011 1v3a1 1 0 01-.293.707L12 11.414V15a1 1 0 01-.293.707l-2 2A1 1 0 018 17v-5.586L3.293 6.707A1 1 0 013 6V3z" clip-rule="evenodd" />
                    </svg>
                  </button>
                </div>
              </th>
              <th class="text-indigo-900">{$t("source")}</th>
              <th class="text-indigo-900">{$t("publication_date")}</th>
              <th class="text-indigo-900">{$t("scraped_at")}</th>
            </tr>
            {#if showFilterRow}
              <tr class="bg-indigo-50/30 transition-all duration-300">
                <td></td>
                <td class="p-2">
                  <div class="flex gap-1 overflow-hidden">
                    <select bind:value={columnFilters.title.operator} class="select select-bordered select-xs bg-white text-[10px] w-20">
                      {#each textOperators as op}
                        <option value={op}>{op.replace("_", " ")}</option>
                      {/each}
                    </select>
                    <input type="text" bind:value={columnFilters.title.value} placeholder="Filter..." class="input input-bordered input-xs flex-1 bg-white" />
                  </div>
                </td>
                <td class="p-2">
                  <select bind:value={columnFilters.source.value} class="select select-bordered select-xs w-full bg-white">
                    <option value="">All</option>
                    {#each uniqueSources as src}
                      <option value={src}>{src}</option>
                    {/each}
                  </select>
                </td>
                <td class="p-2">
                  <div class="flex gap-1">
                    <select bind:value={columnFilters.publication_date.operator} class="select select-bordered select-xs bg-white text-[10px] w-20">
                      {#each dateOperators as op}
                        <option value={op}>{op}</option>
                      {/each}
                    </select>
                    {#if columnFilters.publication_date.operator !== "all"}
                      <input type="date" bind:value={columnFilters.publication_date.value} class="input input-bordered input-xs flex-1 bg-white animate-in slide-in-from-left-2" />
                    {/if}
                  </div>
                </td>
                <td class="p-2">
                  <div class="flex gap-1">
                    <select bind:value={columnFilters.scraped_at.operator} class="select select-bordered select-xs bg-white text-[10px] w-20">
                      {#each dateOperators as op}
                        <option value={op}>{op}</option>
                      {/each}
                    </select>
                    {#if columnFilters.scraped_at.operator !== "all"}
                      <input type="date" bind:value={columnFilters.scraped_at.value} class="input input-bordered input-xs flex-1 bg-white animate-in slide-in-from-left-2" />
                    {/if}
                  </div>
                </td>
              </tr>
            {/if}
          </thead>
          <tbody>
            {#each filteredResults as result (result.id)}
              <tr class="hover transition-colors {selectedIds.has(result.id) ? 'bg-indigo-50/50' : ''}">
                <td>
                  <input type="checkbox" class="checkbox checkbox-sm" checked={selectedIds.has(result.id)} on:change={() => toggleSelect(result.id)} />
                </td>
                <td class="max-w-md">
                  <div class="flex items-start gap-2">
                    <a href={result.url} target="_blank" class="text-blue-600 hover:text-blue-800 font-bold decoration-blue-200 underline underline-offset-4 decoration-2">
                      {result.title}
                    </a>
                    {#if analyzedResultIds.has(result.id)}
                      <span class="badge badge-xs bg-accent text-accent-content font-bold flex-shrink-0 mt-0.5" title="KI-Analyse durchgeführt">KI</span>
                    {/if}
                  </div>
                </td>
                <td><span class="badge badge-ghost font-mono text-xs">{result.source}</span></td>
                <td class="text-gray-600 italic">{result.publication_date}</td>
                <td class="text-gray-500 text-xs">{new Date(result.scraped_at).toLocaleString()}</td>
              </tr>
            {/each}
          </tbody>
        </table>

      <!-- CARDS SMALL VIEW -->
      {:else if viewMode === "cards-small"}
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {#each filteredResults as result (result.id)}
            <div class="bg-white border rounded-xl p-3 flex flex-col gap-2 hover:shadow-md transition-shadow {selectedIds.has(result.id) ? 'ring-2 ring-indigo-400' : ''}">
              <div class="flex items-start gap-2">
                <input type="checkbox" class="checkbox checkbox-xs mt-0.5 flex-shrink-0" checked={selectedIds.has(result.id)} on:change={() => toggleSelect(result.id)} />
                <div class="flex-1 min-w-0">
                  <a href={result.url} target="_blank" class="text-blue-600 hover:text-blue-800 font-semibold text-sm leading-tight line-clamp-3">
                    {result.title}
                  </a>
                </div>
                {#if analyzedResultIds.has(result.id)}
                  <span class="badge badge-xs bg-accent text-accent-content font-bold flex-shrink-0" title="KI-Analyse durchgeführt">KI</span>
                {/if}
              </div>
              <div class="flex justify-between items-center mt-auto">
                <span class="badge badge-ghost badge-xs font-mono truncate max-w-[100px]">{result.source}</span>
                <span class="text-xs text-gray-400">{result.publication_date || "—"}</span>
              </div>
            </div>
          {/each}
        </div>

      <!-- CARDS LARGE VIEW -->
      {:else if viewMode === "cards-large"}
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {#each filteredResults as result (result.id)}
            <div class="bg-white border rounded-xl p-4 flex flex-col gap-3 hover:shadow-md transition-shadow {selectedIds.has(result.id) ? 'ring-2 ring-indigo-400' : ''}">
              <div class="flex items-start gap-3">
                <input type="checkbox" class="checkbox checkbox-sm mt-0.5 flex-shrink-0" checked={selectedIds.has(result.id)} on:change={() => toggleSelect(result.id)} />
                <div class="flex flex-col gap-1 flex-1 min-w-0">
                  <div class="flex items-start gap-2">
                    <a href={result.url} target="_blank" class="text-blue-600 hover:text-blue-800 font-bold text-base leading-snug flex-1">
                      {result.title}
                    </a>
                    {#if analyzedResultIds.has(result.id)}
                      <span class="badge badge-sm bg-accent text-accent-content font-bold flex-shrink-0" title="KI-Analyse durchgeführt">KI</span>
                    {/if}
                  </div>
                  {#if result.description}
                    <p class="text-gray-600 text-sm leading-relaxed line-clamp-2">
                      {result.description.slice(0, 150)}{result.description.length > 150 ? "…" : ""}
                    </p>
                  {/if}
                </div>
              </div>
              <div class="flex justify-between items-center border-t pt-2">
                <span class="badge badge-ghost font-mono text-xs">{result.source}</span>
                <div class="flex gap-3 text-xs text-gray-400">
                  <span>{result.publication_date || "—"}</span>
                  <span>{new Date(result.scraped_at).toLocaleDateString()}</span>
                </div>
                <a href={result.url} target="_blank" class="btn btn-xs btn-outline btn-primary">Öffnen</a>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    {/if}
  </div>
</div>

<!-- AI Analysis Modal -->
{#if showAiModal}
  <div class="modal modal-open">
    <div class="modal-box max-w-3xl max-h-[85vh] flex flex-col">
      <div class="flex justify-between items-center mb-4">
        <h3 class="font-bold text-lg">{$t("ai_analysis")}</h3>
        <button class="btn btn-ghost btn-sm btn-circle" on:click={() => (showAiModal = false)}>✕</button>
      </div>

      <!-- Tabs -->
      <div class="tabs tabs-bordered mb-4">
        <button
          class="tab {aiModalTab === 'current' ? 'tab-active' : ''}"
          on:click={() => (aiModalTab = "current")}
        >
          Aktuelle Analyse
          {#if aiAnalysisLoading}
            <span class="loading loading-spinner loading-xs ml-2"></span>
          {/if}
        </button>
        <button
          class="tab {aiModalTab === 'history' ? 'tab-active' : ''}"
          on:click={() => { aiModalTab = "history"; fetchAiHistory(); }}
        >
          Verlauf
          {#if aiHistory.length > 0}
            <span class="badge badge-sm ml-2">{aiHistory.length}</span>
          {/if}
        </button>
      </div>

      <!-- Current analysis -->
      {#if aiModalTab === "current"}
        {#if aiAnalysisLoading}
          <div class="flex flex-col items-center gap-4 py-8 flex-1">
            <span class="loading loading-spinner loading-lg text-accent"></span>
            <p class="text-gray-500">{$t("ai_analyzing")}</p>
          </div>
        {:else if aiAnalysisError}
          <div class="alert alert-error">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
            </svg>
            <div>
              <p class="font-bold">Fehler bei der KI-Analyse</p>
              <p class="text-sm">{aiAnalysisError}</p>
              <p class="text-xs mt-1 opacity-70">Bitte prüfe die KI-Einstellungen im Admin-Bereich.</p>
            </div>
          </div>
        {:else if aiAnalysisResult}
          <div class="overflow-auto flex-1">
            <pre class="bg-gray-50 rounded-lg p-4 text-sm whitespace-pre-wrap leading-relaxed">{aiAnalysisResult}</pre>
          </div>
        {:else}
          <div class="text-center py-12 text-gray-400">
            <p>Noch keine Analyse gestartet.</p>
            <p class="text-sm mt-1">Ergebnisse auswählen und "KI-Analyse starten" klicken.</p>
          </div>
        {/if}

      <!-- History -->
      {:else if aiModalTab === "history"}
        {#if aiHistoryLoading}
          <div class="flex justify-center py-8">
            <span class="loading loading-spinner text-accent"></span>
          </div>
        {:else if aiHistory.length === 0}
          <div class="text-center py-12 text-gray-400">
            <p>Noch keine gespeicherten Analysen.</p>
          </div>
        {:else}
          <div class="space-y-4 overflow-auto flex-1">
            {#each aiHistory as entry}
              <div class="border rounded-xl overflow-hidden">
                <div class="flex items-center justify-between bg-gray-50 px-4 py-2 border-b">
                  <div class="flex items-center gap-3">
                    <span class="badge badge-sm bg-accent text-accent-content font-bold">KI</span>
                    <span class="text-xs text-gray-500 font-mono">
                      {new Date(entry.created_at).toLocaleString("de-DE")}
                    </span>
                    <span class="text-xs text-gray-400">{entry.result_count} Ergebnisse · {entry.mode}</span>
                  </div>
                </div>
                <pre class="p-4 text-sm whitespace-pre-wrap bg-white leading-relaxed max-h-48 overflow-auto">{entry.result_text}</pre>
              </div>
            {/each}
          </div>
        {/if}
      {/if}

      <div class="modal-action mt-4 pt-3 border-t">
        <button class="btn" on:click={() => (showAiModal = false)}>{$t("close")}</button>
      </div>
    </div>
    <div class="modal-backdrop" on:click={() => (showAiModal = false)}></div>
  </div>
{/if}

<style>
  .custom-scrollbar::-webkit-scrollbar {
    width: 8px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: #1a1a1a;
    border-radius: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: #4f46e5;
    border-radius: 4px;
    border: 2px solid #1a1a1a;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: #6366f1;
  }
  /* For Firefox */
  .custom-scrollbar {
    scrollbar-width: thin;
    scrollbar-color: #4f46e5 #1a1a1a;
  }
</style>
