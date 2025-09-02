<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { api } from '../api';

  const dispatch = createEventDispatcher();

  let address = '';
  let radius = 20; // Default radius in km
  let isLoading = false;
  let errorMessage = '';

  async function search() {
    if (!address) {
      errorMessage = 'Address is required.';
      return;
    }

    isLoading = true;
    errorMessage = '';

    try {
      // Step 1: Geocode the user's address
      const geocodeUrl = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(address)}&format=json&limit=1&countrycodes=de`;
      const geocodeResponse = await fetch(geocodeUrl);
      const geocodeData = await geocodeResponse.json();

      if (!geocodeData || geocodeData.length === 0) {
        throw new Error('Could not find coordinates for the address.');
      }

      const lat = parseFloat(geocodeData[0].lat);
      const lon = parseFloat(geocodeData[0].lon);

      // Step 2: Call our backend to find targets in the radius
      const searchUrl = `/api/targets/search-by-radius/?lat=${lat}&lon=${lon}&radius=${radius}`;
      const nearbyTargets = await api(searchUrl);
      dispatch('searchcomplete', { targets: nearbyTargets, center: { lat, lon } });

    } catch (error) {
      errorMessage = error.message;
    } finally {
      isLoading = false;
    }
  }
</script>

<div class="p-4 border rounded-md bg-gray-50 mb-4">
  <h3 class="font-semibold text-lg mb-2">Search by Radius</h3>
  <form on:submit|preventDefault={search} class="flex flex-col sm:flex-row gap-2">
    <input
      type="text"
      bind:value={address}
      placeholder="Enter an address or city"
      class="input input-bordered w-full"
      required
    />
    <input
      type="number"
      bind:value={radius}
      min="1"
      class="input input-bordered w-24"
    />
    <span class="p-2">km</span>
    <button type="submit" class="btn btn-accent" disabled={isLoading}>
      {#if isLoading}
        Searching...
      {:else}
        Search
      {/if}
    </button>
  </form>
  {#if errorMessage}
    <p class="text-red-500 mt-2">{errorMessage}</p>
  {/if}
</div>
