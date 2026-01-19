<script lang="ts">
  import { createEventDispatcher } from "svelte";
  import { api } from "../api";
  import { t } from "../stores";

  const dispatch = createEventDispatcher();

  let address = "";
  let radius = 20; // Default radius in km
  let isLoading = false;
  let errorMessage = "";

  async function search() {
    if (!address) {
      errorMessage = "Address is required.";
      return;
    }

    isLoading = true;
    errorMessage = "";

    try {
      const geocodeUrl = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(address)}&format=json&limit=1&countrycodes=de`;
      const geocodeResponse = await fetch(geocodeUrl);
      const geocodeData = await geocodeResponse.json();

      if (!geocodeData || geocodeData.length === 0) {
        throw new Error("Could not find coordinates for the address.");
      }

      const lat = parseFloat(geocodeData[0].lat);
      const lon = parseFloat(geocodeData[0].lon);

      const searchUrl = `/api/targets/search-by-radius?lat=${lat}&lon=${lon}&radius=${radius}`;
      const nearbyTargets = await api(searchUrl);
      dispatch("searchcomplete", {
        targets: nearbyTargets,
        center: { lat, lon },
      });
    } catch (error) {
      errorMessage = (error as Error).message;
    } finally {
      isLoading = false;
    }
  }

  async function useMyLocation() {
    if (!navigator.geolocation) {
      errorMessage = "Geolocation is not supported by your browser";
      return;
    }

    isLoading = true;
    errorMessage = "";

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;
        address = `${lat.toFixed(4)}, ${lon.toFixed(4)}`;

        try {
          const searchUrl = `/api/targets/search-by-radius?lat=${lat}&lon=${lon}&radius=${radius}`;
          const nearbyTargets = await api(searchUrl);
          dispatch("searchcomplete", {
            targets: nearbyTargets,
            center: { lat, lon },
          });
        } catch (error) {
          errorMessage = (error as Error).message;
        } finally {
          isLoading = false;
        }
      },
      (error) => {
        errorMessage = "Unable to retrieve your location";
        isLoading = false;
      },
    );
  }
</script>

<div class="p-4 bg-gray-50 rounded-xl border border-gray-200">
  <h3 class="font-bold text-gray-700 mb-3 flex items-center justify-between">
    <div class="flex items-center gap-2">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="h-5 w-5 text-accent"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
        />
      </svg>
      {$t("search_by_radius")}
    </div>
    <button
      type="button"
      on:click={useMyLocation}
      class="btn btn-xs btn-ghost text-accent flex items-center gap-1"
      disabled={isLoading}
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
          d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
        />
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
        />
      </svg>
      {$t("use_my_location")}
    </button>
  </h3>
  <form
    on:submit|preventDefault={search}
    class="flex flex-col sm:flex-row gap-3"
  >
    <div class="flex-grow">
      <input
        type="text"
        bind:value={address}
        placeholder={$t("enter_address")}
        class="input input-bordered w-full bg-white"
        required
      />
    </div>
    <div class="flex items-center gap-2">
      <input
        type="number"
        bind:value={radius}
        min="1"
        class="input input-bordered w-24 bg-white font-bold"
      />
      <span class="text-sm font-medium text-gray-500">km</span>
    </div>
    <button type="submit" class="btn btn-accent shadow-sm" disabled={isLoading}>
      {#if isLoading}
        <span class="loading loading-spinner loading-xs"></span>
      {:else}
        {$t("search")}
      {/if}
    </button>
  </form>
  {#if errorMessage}
    <div class="alert alert-error mt-3 py-2 text-sm">
      <span>{errorMessage}</span>
    </div>
  {/if}
</div>
