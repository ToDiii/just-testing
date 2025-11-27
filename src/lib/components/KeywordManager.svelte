<script lang="ts">
  import { onMount } from "svelte";
  import { api } from "../api";

  type Keyword = {
    id: number;
    word: string;
    category_id: number | null;
  };

  type Category = {
    id: number;
    name: string;
  };

  let keywords: Keyword[] = [];
  let categories: Category[] = [];
  let newKeyword = "";
  let selectedCategoryId: number | null = null;
  let isLoading = true;
  let errorMessage = "";

  async function fetchKeywords() {
    isLoading = true;
    errorMessage = "";
    try {
      keywords = await api("/api/keywords");
    } catch (error) {
      errorMessage = (error as Error).message;
    } finally {
      isLoading = false;
    }
  }

  async function fetchCategories() {
    try {
      categories = await api("/api/categories");
    } catch (error) {
      console.error("Failed to fetch categories:", error);
    }
  }

  async function addKeyword() {
    if (!newKeyword) {
      errorMessage = "Keyword cannot be empty.";
      return;
    }
    try {
      await api("/api/keywords", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          word: newKeyword,
          category_id: selectedCategoryId,
        }),
      });
      newKeyword = "";
      fetchKeywords(); // Refresh the list
    } catch (error) {
      errorMessage = (error as Error).message;
    }
  }

  async function deleteKeyword(id: number) {
    try {
      await api(`/api/keywords/${id}`, {
        method: "DELETE",
      });
      fetchKeywords(); // Refresh the list
    } catch (error) {
      errorMessage = (error as Error).message;
    }
  }

  function getCategoryName(id: number | null) {
    if (!id) return "";
    const cat = categories.find((c) => c.id === id);
    return cat ? `(${cat.name})` : "";
  }

  onMount(() => {
    fetchKeywords();
    fetchCategories();
  });
</script>

<div class="mt-8">
  <h3 class="text-xl font-semibold mb-2">Manage Keywords</h3>
  <form
    on:submit|preventDefault={addKeyword}
    class="flex flex-col sm:flex-row gap-2 mb-4"
  >
    <input
      type="text"
      placeholder="New keyword"
      bind:value={newKeyword}
      class="input input-bordered w-full max-w-xs"
    />
    <select
      bind:value={selectedCategoryId}
      class="select select-bordered w-full max-w-xs"
    >
      <option value={null}>No Category</option>
      {#each categories as category}
        <option value={category.id}>{category.name}</option>
      {/each}
    </select>
    <button
      type="submit"
      class="btn btn-secondary hover:brightness-90 transition-all"
      >Add Keyword</button
    >
  </form>
  {#if errorMessage}
    <p class="text-red-500 my-2">{errorMessage}</p>
  {/if}

  {#if isLoading}
    <p>Loading keywords...</p>
  {:else}
    <div class="flex flex-wrap gap-2">
      {#each keywords as keyword (keyword.id)}
        <div class="badge badge-lg badge-outline gap-2 h-auto py-2">
          <span class="flex flex-col items-start">
            <span>{keyword.word}</span>
            {#if keyword.category_id}
              <span class="text-xs text-gray-500"
                >{getCategoryName(keyword.category_id)}</span
              >
            {/if}
          </span>
          <button
            on:click={() => deleteKeyword(keyword.id)}
            class="btn btn-xs btn-circle btn-ghost hover:bg-red-100"
          >
            ✕
          </button>
        </div>
      {/each}
    </div>
  {/if}
</div>
