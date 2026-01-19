<script lang="ts">
    import { onMount, createEventDispatcher } from "svelte";
    import { api } from "../api";
    import { t } from "../stores";

    const dispatch = createEventDispatcher();

    type Category = {
        id: number;
        name: string;
    };

    let categories: Category[] = [];
    let newCategoryName = "";
    let isLoading = true;
    let errorMessage = "";

    async function fetchCategories() {
        isLoading = true;
        errorMessage = "";
        try {
            categories = await api("/api/categories");
            dispatch("categoriesUpdated", categories);
        } catch (error) {
            errorMessage = (error as Error).message;
        } finally {
            isLoading = false;
        }
    }

    async function addCategory() {
        if (!newCategoryName) {
            errorMessage = "Category name cannot be empty.";
            return;
        }
        try {
            await api("/api/categories", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name: newCategoryName }),
            });
            newCategoryName = "";
            fetchCategories();
        } catch (error) {
            errorMessage = (error as Error).message;
        }
    }

    async function deleteCategory(id: number) {
        try {
            await api(`/api/categories/${id}`, {
                method: "DELETE",
            });
            fetchCategories();
        } catch (error) {
            errorMessage = (error as Error).message;
        }
    }

    onMount(fetchCategories);
</script>

<div class="mt-8">
    <h3 class="text-xl font-semibold mb-4 flex items-center">
        <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-5 w-5 mr-2 text-indigo-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
        >
            <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
            />
        </svg>
        {$t("categories")}
    </h3>
    <form on:submit|preventDefault={addCategory} class="flex gap-2 mb-6">
        <input
            type="text"
            placeholder={$t("category_placeholder")}
            bind:value={newCategoryName}
            class="input input-bordered w-full max-w-xs bg-white"
        />
        <button type="submit" class="btn btn-secondary"
            >{$t("add_category")}</button
        >
    </form>
    {#if errorMessage}
        <div class="alert alert-error mb-4 py-2 text-sm">
            <span>{errorMessage}</span>
        </div>
    {/if}

    {#if isLoading}
        <div class="flex items-center gap-2 text-gray-500 italic">
            <span class="loading loading-spinner loading-xs"></span>
            Lade Kategorien...
        </div>
    {:else}
        <div class="flex flex-wrap gap-3">
            {#each categories as category (category.id)}
                <div
                    class="badge badge-lg badge-primary badge-outline py-4 px-4 gap-2 border-2 group transition-all hover:bg-indigo-50"
                >
                    <span class="font-bold"># {category.name}</span>
                    <button
                        on:click={() => deleteCategory(category.id)}
                        class="text-gray-400 hover:text-red-500 transition-colors"
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
                <p class="text-sm text-gray-400 italic">No categories yet.</p>
            {/each}
        </div>
    {/if}
</div>
