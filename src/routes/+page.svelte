<script lang="ts">
  import { onMount } from 'svelte';
  import Map from '$lib/components/Map.svelte';
  import { api } from '$lib/api';

  let targets = [];

  onMount(async () => {
    try {
      // Fetch all targets from the API to display on the map
      targets = await api('/api/targets?limit=10000'); // Use a high limit to get all targets
    } catch (error) {
      console.error("Failed to fetch targets for map:", error);
    }
  });
</script>

<div class="w-screen h-screen">
  <Map {targets} />
</div>
