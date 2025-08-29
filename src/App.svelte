<script lang="ts">
  import TargetManager from './lib/components/TargetManager.svelte';
  import ResultsViewer from './lib/components/ResultsViewer.svelte';
  import './app.css';

  let currentView: 'targets' | 'results' = 'results';
</script>

<main class="bg-gray-100 min-h-screen font-sans">
  <header class="bg-white shadow">
    <div class="container mx-auto px-4 py-6">
      <h1 class="text-3xl font-bold text-gray-800">Scraper Dashboard</h1>
      <nav class="mt-4">
        <button
          class="px-4 py-2 rounded-md mr-2 {currentView === 'results' ? 'bg-blue-500 text-white' : 'bg-gray-200'}"
          on:click={() => currentView = 'results'}>
          Results
        </button>
        <button
          class="px-4 py-2 rounded-md {currentView === 'targets' ? 'bg-blue-500 text-white' : 'bg-gray-200'}"
          on:click={() => currentView = 'targets'}>
          Manage Targets
        </button>
      </nav>
    </div>
  </header>

  <div class="container mx-auto p-4 mt-6">
    {#if currentView === 'results'}
      <ResultsViewer />
    {:else}
      <TargetManager />
    {/if}
  </div>
</main>
