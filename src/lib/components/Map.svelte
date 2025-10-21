<script lang="ts">
  import 'leaflet/dist/leaflet.css';
  import { LeafletMap, TileLayer, Marker, Popup } from 'svelte-leafletjs';
  import { onMount } from 'svelte';

  export let targets: any[] = [];

  let map: L.Map;
  let L: any;

  // Filter targets that have valid coordinates
  $: markers = targets.filter(t => t.latitude != null && t.longitude != null);

  // Default map center (Germany)
  const mapOptions = {
    center: [51.1657, 10.4515],
    zoom: 6,
  };

  onMount(async () => {
    // Dynamically import Leaflet only on the client side
    L = await import('leaflet');

    // Fix for default icon path issue with bundlers
    // @ts-ignore
    delete L.Icon.Default.prototype._getIconUrl;
    L.Icon.Default.mergeOptions({
      iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
      iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
      shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
    });
  });
</script>

<div class="h-full w-full">
  {#if L}
    <LeafletMap options={mapOptions} bind:map>
      <TileLayer
        url={`https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png`}
        options={{
          attribution: `&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors`,
        }}
      />
      {#each markers as target (target.id)}
        <Marker latLng={[target.latitude, target.longitude]}>
          <Popup>
            <strong>{target.name || 'Unnamed Target'}</strong>
            <br />
            <a href={target.url} target="_blank" rel="noopener noreferrer">Visit website</a>
          </Popup>
        </Marker>
      {/each}
    </LeafletMap>
  {/if}
</div>
