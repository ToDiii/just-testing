<script lang="ts">
  import { onMount } from "svelte";
  import { api } from "../api";
  import KeywordManager from "./KeywordManager.svelte";
  import CategoryManager from "./CategoryManager.svelte";
  import { t, language } from "../stores";
  import { formatDistanceToNow } from "date-fns";
  import { de, enUS } from "date-fns/locale";

  type Target = {
    id: number;
    name: string;
    url: string;
    last_scraped_at: string | null;
  };

  type Region = {
    id: number;
    name: string;
    type: string;
  };

  let targets: Target[] = [];
  let regions: Region[] = [];
  let newTargetName = "";
  let newTargetUrl = "";
  let newTargetRegionId: number | null = null;
  let isLoading = true;
  let errorMessage = "";
  let filterText = "";

  async function fetchRegions() {
    try {
      regions = await api("/api/regions");
    } catch (error) {
      console.error("Failed to fetch regions:", error);
    }
  }

  type ScrapeStatus = {
    last_scrape_start: string | null;
    last_scrape_end: string | null;
    scrape_status: "idle" | "running";
  };

  let scrapeStatus: ScrapeStatus = {
    last_scrape_start: null,
    last_scrape_end: null,
    scrape_status: "idle",
  };

  let isScraping = false;

  async function fetchScrapeStatus() {
    try {
      scrapeStatus = await api("/api/scrape/status");
      isScraping = scrapeStatus.scrape_status === "running";
    } catch (error) {
      console.error("Failed to fetch scrape status:", error);
    }
  }

  async function scrapeAllTargets() {
    isScraping = true;
    errorMessage = "";
    try {
      await api("/api/scrape", { method: "POST" });
      // After scraping, refresh both the targets (for timestamps) and the status
      await fetchTargets();
      await fetchScrapeStatus();
    } catch (error) {
      errorMessage = (error as Error).message;
    } finally {
      isScraping = false;
    }
  }

  $: filteredTargets = targets.filter(
    (target) =>
      target.name?.toLowerCase().includes(filterText.toLowerCase()) ||
      target.url.toLowerCase().includes(filterText.toLowerCase()),
  );

  function formatTimestamp(timestamp: string | null) {
    if (!timestamp) return $t("never");
    const locale = $language === "de" ? de : enUS;
    return `${formatDistanceToNow(new Date(timestamp), { locale, addSuffix: true })}`;
  }

  async function fetchTargets() {
    isLoading = true;
    errorMessage = "";
    try {
      targets = await api("/api/targets");
    } catch (error) {
      errorMessage = (error as Error).message;
    } finally {
      isLoading = false;
    }
  }

  async function addTarget() {
    if (!newTargetUrl) {
      errorMessage = "URL is required.";
      return;
    }
    try {
      await api("/api/targets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newTargetName,
          url: newTargetUrl,
          region_id: newTargetRegionId,
        }),
      });
      newTargetName = "";
      newTargetUrl = "";
      newTargetRegionId = null;
      fetchTargets(); // Refresh the list
    } catch (error) {
      errorMessage = (error as Error).message;
    }
  }

  onMount(() => {
    fetchTargets();
    fetchRegions();
    fetchScrapeStatus();
  });
</script>

<div class="bg-white p-8 rounded-xl shadow-lg border border-gray-100">
  <div
    class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4 border-b pb-6"
  >
    <div>
      <h2 class="text-3xl font-extrabold text-gray-900 tracking-tight">
        {$t("manage_targets_keywords")}
      </h2>
      <p class="text-gray-500 mt-1">
        Configure sources, categories and search terms
      </p>
    </div>
    <a
      href="/api/docs"
      target="_blank"
      class="btn btn-outline btn-sm gap-2 rounded-full px-4 hover:bg-gray-100 border-gray-200"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="h-4 w-4"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
        />
      </svg>
      API Docs
    </a>
  </div>

  <div class="grid grid-cols-1 xl:grid-cols-12 gap-10">
    <div class="xl:col-span-7 space-y-10">
      <section class="bg-gray-50 p-6 rounded-2xl border border-gray-100">
        <h3 class="text-xl font-bold mb-6 flex items-center">
          <div
            class="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center mr-3 shadow-indigo-100 shadow-lg"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-5 w-5 text-white"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 9v3m0 0v3m0-3h3m-3 0H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          {$t("add_target")}
        </h3>
        <form on:submit|preventDefault={addTarget} class="space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input
              type="text"
              placeholder={$t("name") + " (z.B. Berlin)"}
              bind:value={newTargetName}
              class="input input-bordered w-full bg-white focus:ring-2 focus:ring-indigo-200 transition-all"
            />
            <input
              type="url"
              placeholder={$t("url")}
              required
              bind:value={newTargetUrl}
              class="input input-bordered w-full bg-white focus:ring-2 focus:ring-indigo-200 transition-all"
            />
          </div>
          <select
            bind:value={newTargetRegionId}
            class="select select-bordered w-full bg-white"
          >
            <option value={null}>{$t("select_region_optional")}</option>
            {#each regions as region (region.id)}
              <option value={region.id}>{region.name} ({region.type})</option>
            {/each}
          </select>
          <button
            type="submit"
            class="btn btn-primary btn-block shadow-lg shadow-indigo-100"
            >{$t("add_target")}</button
          >
        </form>

        {#if errorMessage}
          <div class="alert alert-error mt-4 shadow-sm text-sm py-2">
            <span>{errorMessage}</span>
          </div>
        {/if}
      </section>

      <section>
        <div
          class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4"
        >
          <h4 class="text-xl font-bold text-gray-800">
            {$t("existing_targets")}
          </h4>
          <button
            class="btn btn-secondary btn-sm gap-2"
            on:click={scrapeAllTargets}
            disabled={isScraping}
          >
            {#if isScraping}
              <span class="loading loading-spinner loading-xs"></span>
              {$t("active")}
            {:else}
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              {$t("scrape_all_targets")}
            {/if}
          </button>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
          <div class="bg-indigo-50 p-4 rounded-xl border border-indigo-100">
            <p
              class="text-[10px] uppercase font-bold text-indigo-400 tracking-wider"
            >
              {$t("last_scrape_started")}
            </p>
            <p class="text-sm font-semibold text-indigo-900">
              {formatTimestamp(scrapeStatus.last_scrape_start)}
            </p>
          </div>
          <div class="bg-green-50 p-4 rounded-xl border border-green-100">
            <p
              class="text-[10px] uppercase font-bold text-green-400 tracking-wider"
            >
              {$t("last_scrape_finished")}
            </p>
            <p class="text-sm font-semibold text-green-900">
              {formatTimestamp(scrapeStatus.last_scrape_end)}
            </p>
          </div>
        </div>

        <div class="relative mb-6">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-5 w-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            type="text"
            placeholder={$t("filter_targets")}
            bind:value={filterText}
            class="input input-bordered w-full pl-10 bg-gray-50 border-gray-200 focus:bg-white transition-all"
          />
        </div>

        {#if isLoading}
          <div class="flex justify-center p-12">
            <span class="loading loading-spinner text-indigo-600"></span>
          </div>
        {:else if targets.length === 0}
          <div
            class="text-center py-12 bg-gray-50 rounded-2xl border-2 border-dashed border-gray-200"
          >
            <p class="text-gray-400">{$t("no_targets_configured")}</p>
          </div>
        {:else if filteredTargets.length === 0}
          <div
            class="text-center py-12 bg-gray-50 rounded-2xl border-2 border-dashed border-gray-200"
          >
            <p class="text-gray-400">{$t("no_targets_match")}</p>
          </div>
        {:else}
          <div
            class="overflow-x-auto rounded-xl border border-gray-100 shadow-sm"
          >
            <table class="table w-full">
              <thead>
                <tr class="bg-gray-50">
                  <th class="text-gray-600">{$t("name")}</th>
                  <th class="text-gray-600">{$t("url")}</th>
                  <th class="text-gray-600">{$t("last_scraped")}</th>
                </tr>
              </thead>
              <tbody>
                {#each filteredTargets as target (target.id)}
                  <tr class="hover:bg-indigo-50/30 transition-colors">
                    <td class="font-bold text-gray-900"
                      >{target.name || "Unnamed"}</td
                    >
                    <td
                      class="text-xs text-gray-500 max-w-[200px] truncate"
                      title={target.url}>{target.url}</td
                    >
                    <td class="text-xs font-mono text-indigo-600"
                      >{formatTimestamp(target.last_scraped_at)}</td
                    >
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {/if}
      </section>
    </div>

    <div class="xl:col-span-5 space-y-10 border-l pl-0 xl:pl-10">
      <CategoryManager />
      <div class="pt-6 border-t border-gray-100">
        <KeywordManager />
      </div>
    </div>
  </div>
</div>
