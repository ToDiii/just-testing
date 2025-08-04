<script lang="ts">
  import { onMount, createEventDispatcher } from 'svelte';
  import maplibregl, { Map } from 'maplibre-gl';
  import 'maplibre-gl/dist/maplibre-gl.css';

  const DEFAULT_STYLE = 'https://demotiles.maplibre.org/style.json';
  const styleUrl = import.meta.env.VITE_MAP_STYLE || DEFAULT_STYLE;

  const dispatch = createEventDispatcher<{ load: { map: Map } }>();

  let container: HTMLDivElement;
  let map: Map;

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

    return () => map.remove();
  });
</script>

<div bind:this={container} class="w-full h-full"></div>
