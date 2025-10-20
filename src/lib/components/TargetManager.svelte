<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '../api';
  import KeywordManager from './KeywordManager.svelte';
  import { formatDistanceToNow } from 'date-fns';

  type Target = {
    id: number;
    name: string;
    url: string;
    last_scraped_at: string | null;
  };

  let targets: Target[] = [];
  let newTargetName = '';
  let newTargetUrl = '';
  let isLoading = true;
  let errorMessage = '';
  let filterText = '';

  type ScrapeStatus = {
    last_scrape_start: string | null;
    last_scrape_end: string | null;
    scrape_status: 'idle' | 'running';
  };

  let scrapeStatus: ScrapeStatus = {
    last_scrape_start: null,
    last_scrape_end: null,
    scrape_status: 'idle',
  };

  let isScraping = false;

  async function fetchScrapeStatus() {
    try {
      scrapeStatus = await api('/api/scrape/status');
      isScraping = scrapeStatus.scrape_status === 'running';
    } catch (error) {
      console.error('Failed to fetch scrape status:', error);
    }
  }

  async function scrapeAllTargets() {
    isScraping = true;
    errorMessage = '';
    try {
      await api('/api/scrape', { method: 'POST' });
      // After scraping, refresh both the targets (for timestamps) and the status
      await fetchTargets();
      await fetchScrapeStatus();
    } catch (error) {
      errorMessage = error.message;
    } finally {
      isScraping = false;
    }
  }

  $: filteredTargets = targets.filter(target =>
    target.name?.toLowerCase().includes(filterText.toLowerCase()) ||
    target.url.toLowerCase().includes(filterText.toLowerCase())
  );

  function formatTimestamp(timestamp: string | null) {
    if (!timestamp) return 'Never';
    return `${formatDistanceToNow(new Date(timestamp))} ago`;
  }

  async function fetchTargets() {
    isLoading = true;
    errorMessage = '';
    try {
      targets = await api('/api/targets/');
    } catch (error) {
      errorMessage = error.message;
    } finally {
      isLoading = false;
    }
  }

  async function addTarget() {
    if (!newTargetUrl) {
      errorMessage = 'URL is required.';
      return;
    }
    try {
      await api('/api/targets/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newTargetName, url: newTargetUrl }),
      });
      newTargetName = '';
      newTargetUrl = '';
      fetchTargets(); // Refresh the list
    } catch (error) {
      errorMessage = error.message;
    }
  }

  onMount(() => {
    fetchTargets();
    fetchScrapeStatus();
  });
</script>

<div class="bg-white p-6 rounded-lg shadow-md">
  <div class="flex justify-between items-center mb-4">
    <h2 class="text-2xl font-bold">Manage Targets & Keywords</h2>
    <a href="/api/docs" target="_blank" class="btn btn-ghost">
      API Docs
      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
      </svg>
    </a>
  </div>

  <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
    <div>
      <h3 class="text-xl font-semibold mb-2">Manage Targets</h3>
      <form on:submit|preventDefault={addTarget} class="mb-6">
        <div class="flex flex-col gap-2 mb-2">
          <input
            type="text"
            placeholder="Name (e.g., City Name)"
            bind:value={newTargetName}
            class="input input-bordered w-full"
          />
          <input
            type="url"
            placeholder="URL"
            required
            bind:value={newTargetUrl}
            class="input input-bordered w-full"
          />
        </div>
        <button type="submit" class="btn btn-primary">Add Target</button>
      </form>

      {#if errorMessage}
        <p class="text-red-500 my-2">{errorMessage}</p>
      {/if}

      <div>
        <div class="flex justify-between items-center mb-4">
          <h4 class="font-semibold">Existing Targets</h4>
          <button
            class="btn btn-secondary"
            on:click={scrapeAllTargets}
            disabled={isScraping}
          >
            {#if isScraping}
              <span class="loading loading-spinner"></span>
              Scraping...
            {:else}
              Scrape All Targets
            {/if}
          </button>
        </div>

        <div class="text-sm text-gray-500 mb-4 p-2 bg-gray-50 rounded-md">
          <p>Last scrape started: {formatTimestamp(scrapeStatus.last_scrape_start)}</p>
          <p>Last scrape finished: {formatTimestamp(scrapeStatus.last_scrape_end)}</p>
        </div>

        <input
          type="text"
          placeholder="Filter targets..."
          bind:value={filterText}
          class="input input-bordered w-full mb-4"
        />
        {#if isLoading}
          <p>Loading targets...</p>
        {:else if targets.length === 0}
          <p>No targets configured yet.</p>
        {:else if filteredTargets.length === 0}
          <p>No targets match your filter.</p>
        {:else}
          <div class="overflow-x-auto">
            <table class="table w-full">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>URL</th>
                  <th>Last Scraped</th>
                </tr>
              </thead>
              <tbody>
                {#each filteredTargets as target (target.id)}
                  <tr>
                    <td class="font-bold">{target.name || 'Unnamed'}</td>
                    <td class="text-sm break-all">{target.url}</td>
                    <td class="text-sm">{formatTimestamp(target.last_scraped_at)}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {/if}
      </div>
    </div>

    <div>
      <KeywordManager />
    </div>
  </div>
</div>
