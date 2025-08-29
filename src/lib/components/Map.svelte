<script lang="ts">
  import { onMount, createEventDispatcher } from 'svelte';
  import maplibregl, { Map } from 'maplibre-gl';
  import 'maplibre-gl/dist/maplibre-gl.css';

  const DEFAULT_STYLE = 'https://demotiles.maplibre.org/style.json';
  const styleUrl = import.meta.env.VITE_MAP_STYLE || DEFAULT_STYLE;

  const dispatch = createEventDispatcher<{ load: { map: Map } }>();

  let container: HTMLDivElement;
  export let map: Map = undefined;

  let markers = [];

  export function addMarkers(locations: { lon: number; lat: number; name: string }[]) {
    // Clear existing markers
    markers.forEach(marker => marker.remove());
    markers = [];

    if (!map) return;

    locations.forEach(loc => {
      const marker = new maplibregl.Marker()
        .setLngLat([loc.lon, loc.lat])
        .setPopup(new maplibregl.Popup().setText(loc.name))
        .addTo(map);
      markers.push(marker);
    });

    if (locations.length > 0) {
      const bounds = new maplibregl.LngLatBounds();
      locations.forEach(loc => bounds.extend([loc.lon, loc.lat]));
      map.fitBounds(bounds, { padding: 50 });
    }
  }

  onMount(() => {
    map = new maplibregl.Map({
      container,
      style: styleUrl,
      center: [11.576124, 48.137154],
      zoom: 10
    });

    map.addControl(new maplibregl.NavigationControl(), 'top-right');
    map.addControl(new maplibregl.ScaleControl(), 'bottom-left');

    map.on('load', () => dispatch('load', { map }));

    return () => {
      markers.forEach(marker => marker.remove());
      map.remove();
    };
  });
</script>

<div bind:this={container} class="w-full h-full"></div>
