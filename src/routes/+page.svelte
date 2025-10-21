<script lang="ts">
  import Map from '$lib/components/Map.svelte';

  function handleLoad(event: CustomEvent) {
    const map = event.detail.map;
    // Placeholder for dynamic layer handling
    console.log('Map loaded', map);
  }
</script>

<div class="w-screen h-screen">
  <Map on:load={handleLoad} />
</div>
