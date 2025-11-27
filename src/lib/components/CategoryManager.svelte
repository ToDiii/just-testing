<script lang="ts">
    import { onMount, createEventDispatcher } from "svelte";
    import { api } from "../api";

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
    <h3 class="text-xl font-semibold mb-2">Manage Categories</h3>
    <form on:submit|preventDefault={addCategory} class="flex gap-2 mb-4">
        <input
            type="text"
            placeholder="New category"
            bind:value={newCategoryName}
            class="input input-bordered w-full max-w-xs"
        />
        <button
            type="submit"
            class="btn btn-secondary hover:brightness-90 transition-all"
            >Add Category</button
        >
    </form>
    {#if errorMessage}
        <p class="text-red-500 my-2">{errorMessage}</p>
    {/if}

    {#if isLoading}
        <p>Loading categories...</p>
    {:else}
        <div class="flex flex-wrap gap-2">
            {#each categories as category (category.id)}
                <div class="badge badge-lg badge-primary badge-outline gap-2">
                    {category.name}
                    <button
                        on:click={() => deleteCategory(category.id)}
                        class="btn btn-xs btn-circle btn-ghost hover:bg-red-100"
                    >
                        ✕
                    </button>
                </div>
            {/each}
        </div>
    {/if}
</div>
