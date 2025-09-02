<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '../api';

  type Keyword = {
    id: number;
    word: string;
  };

  let keywords: Keyword[] = [];
  let newKeyword = '';
  let isLoading = true;
  let errorMessage = '';

  async function fetchKeywords() {
    isLoading = true;
    errorMessage = '';
    try {
      keywords = await api('/api/keywords/');
    } catch (error) {
      errorMessage = error.message;
    } finally {
      isLoading = false;
    }
  }

  async function addKeyword() {
    if (!newKeyword) {
      errorMessage = 'Keyword cannot be empty.';
      return;
    }
    try {
      await api('/api/keywords/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ word: newKeyword }),
      });
      newKeyword = '';
      fetchKeywords(); // Refresh the list
    } catch (error) {
      errorMessage = error.message;
    }
  }

  async function deleteKeyword(id: number) {
    try {
      await api(`/api/keywords/${id}`, {
        method: 'DELETE',
      });
      fetchKeywords(); // Refresh the list
    } catch (error) {
      errorMessage = error.message;
    }
  }

  onMount(fetchKeywords);
</script>

<div class="mt-8">
  <h3 class="text-xl font-semibold mb-2">Manage Keywords</h3>
  <form on:submit|preventDefault={addKeyword} class="flex gap-2 mb-4">
    <input
      type="text"
      placeholder="New keyword"
      bind:value={newKeyword}
      class="input input-bordered w-full max-w-xs"
    />
    <button type="submit" class="btn btn-secondary">Add Keyword</button>
  </form>
  {#if errorMessage}
    <p class="text-red-500 my-2">{errorMessage}</p>
  {/if}

  {#if isLoading}
    <p>Loading keywords...</p>
  {:else}
    <div class="flex flex-wrap gap-2">
      {#each keywords as keyword (keyword.id)}
        <div class="badge badge-lg badge-outline gap-2">
          {keyword.word}
          <button
            on:click={() => deleteKeyword(keyword.id)}
            class="btn btn-xs btn-circle btn-ghost"
          >
            ✕
          </button>
        </div>
      {/each}
    </div>
  {/if}
</div>
