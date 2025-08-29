<script lang="ts">
  import { onMount } from 'svelte';

  type Target = {
    id: number;
    name: string;
    url: string;
  };

  let targets: Target[] = [];
  let newTargetName = '';
  let newTargetUrl = '';
  let isLoading = true;
  let errorMessage = '';

  async function fetchTargets() {
    isLoading = true;
    errorMessage = '';
    try {
      const response = await fetch('/api/targets/');
      if (!response.ok) {
        throw new Error('Failed to fetch targets.');
      }
      targets = await response.json();
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
      const response = await fetch('/api/targets/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newTargetName, url: newTargetUrl }),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to add target.');
      }
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
  <h2 class="text-2xl font-bold mb-4">Manage Targets</h2>

  <div class="mb-6">
    <h3 class="text-xl font-semibold mb-2">Add New Target</h3>
    <form on:submit|preventDefault={addTarget}>
      <div class="flex flex-col md:flex-row gap-4 mb-2">
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
      <p class="text-red-500 mt-2">{errorMessage}</p>
    {/if}
  </div>

  <div>
    <h3 class="text-xl font-semibold mb-2">Existing Targets</h3>
    {#if isLoading}
      <p>Loading targets...</p>
    {:else if targets.length === 0}
      <p>No targets configured yet.</p>
    {:else}
      <ul class="space-y-2">
        {#each targets as target (target.id)}
          <li class="p-4 bg-gray-50 rounded-md border border-gray-200">
            <p class="font-bold text-gray-800">{target.name || 'Unnamed'}</p>
            <p class="text-sm text-gray-600">{target.url}</p>
          </li>
        {/each}
      </ul>
    {/if}
  </div>
</div>
