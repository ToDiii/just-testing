<script lang="ts">
  import { onMount } from "svelte";
  import { api } from "../api";
  import { t } from "../stores";

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
  <h3 class="text-xl font-semibold mb-4 flex items-center">
    <svg
      xmlns="http://www.w3.org/2000/svg"
      class="h-5 w-5 mr-2 text-purple-500"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14"
      />
    </svg>
    {$t("keywords")}
  </h3>
  <form
    on:submit|preventDefault={addKeyword}
    class="flex flex-col sm:flex-row gap-2 mb-6"
  >
    <input
      type="text"
      placeholder={$t("keyword_placeholder")}
      bind:value={newKeyword}
      class="input input-bordered w-full max-w-xs bg-white"
    />
    <select
      bind:value={selectedCategoryId}
      class="select select-bordered w-full max-w-xs bg-white"
    >
      <option value={null}>{$t("select_category")}</option>
      {#each categories as category}
        <option value={category.id}>{category.name}</option>
      {/each}
    </select>
    <button type="submit" class="btn btn-secondary">{$t("add_keyword")}</button>
  </form>
  {#if errorMessage}
    <div class="alert alert-error mb-4 py-2 text-sm">
      <span>{errorMessage}</span>
    </div>
  {/if}

  {#if isLoading}
    <div class="flex items-center gap-2 text-gray-500 italic">
      <span class="loading loading-spinner loading-xs"></span>
      Lade Stichworte...
    </div>
  {:else}
    <div class="flex flex-wrap gap-3">
      {#each keywords as keyword (keyword.id)}
        <div
          class="badge badge-lg badge-outline gap-3 h-auto py-2 px-4 border-2 transition-all hover:bg-purple-50"
        >
          <span class="flex flex-col items-start">
            <span class="font-semibold text-gray-800">{keyword.word}</span>
            {#if keyword.category_id}
              <span class="text-[10px] uppercase font-bold text-gray-400"
                >{getCategoryName(keyword.category_id)}</span
              >
            {/if}
          </span>
          <button
            on:click={() => deleteKeyword(keyword.id)}
            class="text-gray-300 hover:text-red-500 transition-colors"
            title={$t("delete")}
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
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      {:else}
        <p class="text-sm text-gray-400 italic">No keywords yet.</p>
      {/each}
    </div>
  {/if}
</div>
