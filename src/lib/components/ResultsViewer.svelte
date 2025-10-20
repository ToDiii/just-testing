<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '../api';

  type ScrapeResult = {
    id: number;
    title: string;
    description: string;
    url: string;
    source: string;
    publication_date: string;
    scraped_at: string;
  };

  let results: ScrapeResult[] = [];
  let isLoading = true;
  let isScraping = false;
  let errorMessage = '';
  let filterSearch = '';

  async function fetchResults() {
    isLoading = true;
    errorMessage = '';
    const params = new URLSearchParams();
    if (filterSearch) params.append('search', filterSearch);

    try {
      results = await api(`/api/results/?${params.toString()}`);
    } catch (error) {
      errorMessage = error.message;
    } finally {
      isLoading = false;
    }
  }

  async function runScrape() {
    isScraping = true;
    errorMessage = '';
    try {
      await api('/api/scrape', { method: 'POST' });
      await fetchResults(); // Refresh results after scrape
    } catch (error) {
      errorMessage = error.message;
    } finally {
      isScraping = false;
    }
  }

  onMount(fetchResults);
</script>

<div class="bg-white p-6 rounded-lg shadow-md">
  <div class="flex justify-between items-center mb-4">
    <h2 class="text-2xl font-bold">Scrape Results</h2>
    <button class="btn btn-primary" on:click={runScrape} disabled={isScraping}>
      {#if isScraping}
        <span class="loading loading-spinner"></span>
        Scraping...
      {:else}
        Run Scrape
      {/if}
    </button>
  </div>

  <div class="mb-4">
    <input
      type="text"
      placeholder="Filter by keyword..."
      bind:value={filterSearch}
      on:input={() => fetchResults()}
      class="input input-bordered w-full"
    />
  </div>

  {#if errorMessage}
    <p class="text-red-500 my-2">{errorMessage}</p>
  {/if}

  <div class="overflow-x-auto">
    {#if isLoading}
      <p>Loading results...</p>
    {:else if results.length === 0}
      <p>No results found. Try running a scrape.</p>
    {:else}
      <table class="table w-full">
        <thead>
          <tr>
            <th>Title</th>
            <th>Source</th>
            <th>Publication Date</th>
            <th>Scraped At</th>
          </tr>
        </thead>
        <tbody>
          {#each results as result (result.id)}
            <tr class="hover">
              <td><a href={result.url} target="_blank" class="link link-primary">{result.title}</a></td>
              <td>{result.source}</td>
              <td>{result.publication_date}</td>
              <td>{new Date(result.scraped_at).toLocaleString()}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </div>
</div>
