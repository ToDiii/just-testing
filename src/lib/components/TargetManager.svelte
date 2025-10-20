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

  onMount(fetchTargets);
</script>

<div class="bg-white p-6 rounded-lg shadow-md">
  <h2 class="text-2xl font-bold mb-4">Manage Targets & Keywords</h2>

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
        <h4 class="font-semibold mb-2">Existing Targets</h4>
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
