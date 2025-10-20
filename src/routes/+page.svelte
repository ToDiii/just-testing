<script lang="ts">
  import { onMount } from 'svelte';
  import Map from '$lib/components/Map.svelte';
  import RadiusSearch from '$lib/components/RadiusSearch.svelte';
  import { api } from '$lib/api';

  let allTargets = [];
  let displayedTargets = [];

  function handleSearchComplete(event) {
    const { targets: foundTargets } = event.detail;
    displayedTargets = foundTargets;
  }

  function resetView() {
    displayedTargets = allTargets;
  }

  onMount(async () => {
    try {
      allTargets = await api('/api/targets?limit=10000');
      displayedTargets = allTargets;
    } catch (error) {
      console.error("Failed to fetch targets for map:", error);
    }
  });
</script>

<div class="w-screen h-screen flex flex-col">
  <div class="p-4 bg-gray-100 shadow-md z-10">
    <RadiusSearch on:searchcomplete={handleSearchComplete} />
    <button class="btn btn-sm btn-secondary mt-2" on:click={resetView}>Reset View</button>
  </div>
  <div class="flex-grow">
    <Map targets={displayedTargets} />
  </div>
</div>
