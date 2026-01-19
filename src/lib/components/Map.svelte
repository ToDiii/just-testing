<script lang="ts">
  import "leaflet/dist/leaflet.css";
  import { LeafletMap, TileLayer, Marker, Popup } from "svelte-leafletjs";
  import { onMount, createEventDispatcher } from "svelte";
  import { t } from "../stores";

  const dispatch = createEventDispatcher();
  export let targets: any[] = [];

  let map: L.Map;
  let L: any;

  // Filter targets that have valid coordinates
  $: markers = targets.filter((t) => t.latitude != null && t.longitude != null);

  // Default map center (Germany)
  const mapOptions = {
    center: [51.1657, 10.4515],
    zoom: 6,
  };

  onMount(async () => {
    // Dynamically import Leaflet only on the client side
    L = await import("leaflet");

    // Fix for default icon path issue with bundlers
    // @ts-ignore
    delete L.Icon.Default.prototype._getIconUrl;
    L.Icon.Default.mergeOptions({
      iconRetinaUrl:
        "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
      iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
      shadowUrl:
        "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    });
  });

  export let viewCenter: [number, number] | null = null;
  export let bounds: [number, number][] | null = null;
  let userLocation: [number, number] | null = null;

  async function locateMe() {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        userLocation = [position.coords.latitude, position.coords.longitude];
        if (map) {
          map.setView(userLocation, 13);
        }
      },
      (error) => {
        console.error("Error getting location:", error);
        alert("Unable to retrieve your location");
      },
    );
  }

  $: if (map && bounds && bounds.length > 0) {
    map.fitBounds(bounds, { padding: [50, 50] });
  }

  $: if (map && viewCenter) {
    const isGermanyCenter = Math.abs(viewCenter[0] - 51.1657) < 0.01;
    map.setView(viewCenter, isGermanyCenter ? 6 : 13);
  }
</script>

<div class="h-full w-full relative">
  <div class="absolute top-4 right-4 z-[1000] flex flex-col gap-2">
    <button
      on:click={locateMe}
      class="group relative flex items-center justify-center w-12 h-12 bg-white/80 backdrop-blur-md border border-white/20 rounded-2xl shadow-[0_8px_32px_0_rgba(31,38,135,0.15)] hover:bg-white hover:scale-110 active:scale-95 transition-all duration-300 overflow-visible"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="h-6 w-6 text-indigo-600 group-hover:animate-pulse"
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

      <!-- Tooltip -->
      <span
        class="absolute right-14 px-3 py-1.5 bg-gray-900/90 backdrop-blur-sm text-white text-xs font-bold rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-all duration-300 translate-x-2 group-hover:translate-x-0 whitespace-nowrap shadow-xl"
      >
        {$t("locate_me")}
      </span>
    </button>
  </div>

  {#if L}
    <LeafletMap options={mapOptions} bind:map>
      <TileLayer
        url={`https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png`}
        options={{
          attribution: `&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors`,
        }}
      />

      {#if userLocation}
        <Marker latLng={userLocation}>
          <Popup>
            <div class="p-1">
              <strong class="block text-blue-600 font-bold"
                >Your Location</strong
              >
            </div>
          </Popup>
        </Marker>
      {/if}

      {#each markers as target (target.id)}
        <Marker latLng={[target.latitude, target.longitude]}>
          <Popup>
            <div class="p-1">
              <strong class="block text-lg mb-1"
                >{target.name || "Unnamed Target"}</strong
              >
              <div class="flex flex-col gap-2 mt-2">
                <a
                  href={target.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  class="text-blue-600 hover:underline text-sm"
                  >🌐 Visit website</a
                >
                <button
                  on:click={() => dispatch("focus", target.id)}
                  class="btn btn-xs btn-primary mt-2"
                >
                  🎯 {$t("focus_on_target")}
                </button>
              </div>
            </div>
          </Popup>
        </Marker>
      {/each}
    </LeafletMap>
  {/if}
</div>
