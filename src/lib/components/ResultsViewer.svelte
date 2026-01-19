<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { api } from "../api";
  import { uiState, t } from "../stores";

  export let forcedTargetIds: number[] | null = null;

  $: if (forcedTargetIds) {
    fetchResults();
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

  <!-- Results Table -->
  <div class="overflow-x-auto">
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
      <div class="flex justify-between items-center mb-4">
        <div class="flex items-center gap-4">
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
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-4 w-4 mr-1"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
              Löschen ({selectedIds.size})
            </button>
          {/if}
        </div>
      </div>

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
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="h-3 w-3"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                  >
                    <path
                      fill-rule="evenodd"
                      d="M3 3a1 1 0 011-1h12a1 1 0 011 1v3a1 1 0 01-.293.707L12 11.414V15a1 1 0 01-.293.707l-2 2A1 1 0 018 17v-5.586L3.293 6.707A1 1 0 013 6V3z"
                      clip-rule="evenodd"
                    />
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
                  <select
                    bind:value={columnFilters.title.operator}
                    class="select select-bordered select-xs bg-white text-[10px] w-20"
                  >
                    {#each textOperators as op}
                      <option value={op}>{op.replace("_", " ")}</option>
                    {/each}
                  </select>
                  <input
                    type="text"
                    bind:value={columnFilters.title.value}
                    placeholder="Filter..."
                    class="input input-bordered input-xs flex-1 bg-white"
                  />
                </div>
              </td>
              <td class="p-2">
                <select
                  bind:value={columnFilters.source.value}
                  class="select select-bordered select-xs w-full bg-white"
                >
                  <option value="">All</option>
                  {#each uniqueSources as src}
                    <option value={src}>{src}</option>
                  {/each}
                </select>
              </td>
              <td class="p-2">
                <div class="flex gap-1">
                  <select
                    bind:value={columnFilters.publication_date.operator}
                    class="select select-bordered select-xs bg-white text-[10px] w-20"
                  >
                    {#each dateOperators as op}
                      <option value={op}>{op}</option>
                    {/each}
                  </select>
                  {#if columnFilters.publication_date.operator !== "all"}
                    <input
                      type="date"
                      bind:value={columnFilters.publication_date.value}
                      class="input input-bordered input-xs flex-1 bg-white animate-in slide-in-from-left-2"
                    />
                  {/if}
                </div>
              </td>
              <td class="p-2">
                <div class="flex gap-1">
                  <select
                    bind:value={columnFilters.scraped_at.operator}
                    class="select select-bordered select-xs bg-white text-[10px] w-20"
                  >
                    {#each dateOperators as op}
                      <option value={op}>{op}</option>
                    {/each}
                  </select>
                  {#if columnFilters.scraped_at.operator !== "all"}
                    <input
                      type="date"
                      bind:value={columnFilters.scraped_at.value}
                      class="input input-bordered input-xs flex-1 bg-white animate-in slide-in-from-left-2"
                    />
                  {/if}
                </div>
              </td>
            </tr>
          {/if}
        </thead>
        <tbody>
          {#each filteredResults as result (result.id)}
            <tr
              class="hover transition-colors {selectedIds.has(result.id)
                ? 'bg-indigo-50/50'
                : ''}"
            >
              <td>
                <input
                  type="checkbox"
                  class="checkbox checkbox-sm"
                  checked={selectedIds.has(result.id)}
                  on:change={() => toggleSelect(result.id)}
                />
              </td>
              <td class="max-w-md">
                <a
                  href={result.url}
                  target="_blank"
                  class="text-blue-600 hover:text-blue-800 font-bold decoration-blue-200 underline underline-offset-4 decoration-2"
                >
                  {result.title}
                </a>
              </td>
              <td
                ><span class="badge badge-ghost font-mono text-xs"
                  >{result.source}</span
                ></td
              >
              <td class="text-gray-600 italic">{result.publication_date}</td>
              <td class="text-gray-500 text-xs"
                >{new Date(result.scraped_at).toLocaleString()}</td
              >
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </div>
</div>

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
