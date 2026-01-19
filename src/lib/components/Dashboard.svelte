<script lang="ts">
    import { onMount } from "svelte";
    import Map from "./Map.svelte";
    import RadiusSearch from "./RadiusSearch.svelte";
    import ResultsViewer from "./ResultsViewer.svelte";
    import { api } from "../api";
    import { t } from "../stores";

    let allTargets: any[] = [];
    let displayedTargets: any[] = [];
    let mapCenter: [number, number] | null = null;
    let mapBounds: [number, number][] | null = null;
    let isLoading = false;
    let message = "";

    import { uiState } from "../stores";

    onMount(async () => {
        isLoading = true;
        try {
            allTargets = await api("/api/targets?limit=10000");
            console.log("Loaded targets:", allTargets.length);
            displayedTargets = allTargets;
        } catch (error) {
            console.error("Failed to fetch targets:", error);
        } finally {
            isLoading = false;
        }
    });

    async function stopScrape() {
        try {
            message = "Abbruch angefordert... bitte warten...";
            await api("/api/scrape/stop", { method: "POST" });
        } catch (error: any) {
            message = "Fehler beim Stoppen: " + error.message;
        }
    }

    function handleSearchComplete(event: any) {
        const { targets, center } = event.detail;
        displayedTargets = targets;

        // Calculate bounds to include all targets AND the search center
        const points: [number, number][] = targets
            .filter((t: any) => t.latitude != null && t.longitude != null)
            .map((t: any) => [t.latitude, t.longitude] as [number, number]);

        if (center) {
            points.push([center.lat, center.lon]);
        }

        if (points.length > 0) {
            mapBounds = points;
        } else if (center) {
            mapCenter = [center.lat, center.lon];
        }
    }

    function handleFocus(event: any) {
        const targetId = event.detail;
        displayedTargets = allTargets.filter((t) => t.id === targetId);
        message = "";
    }

    function resetView() {
        displayedTargets = allTargets;
        mapCenter = [51.1657, 10.4515]; // Deutschland Mitte
        mapBounds = null;
        // Trigger a re-render/re-fit for the map by setting a small timeout
        setTimeout(() => {
            mapCenter = [51.1657, 10.4516]; // Tiny change to trigger reactivity
        }, 10);
    }

    async function scrapeVisible() {
        if (displayedTargets.length === 0) return;
        isLoading = true;
        message = "";
        try {
            const targetIds = displayedTargets.map((t) => t.id).join(",");
            await api(`/api/scrape?target_ids=${targetIds}`, {
                method: "POST",
            });
            message = `Scrape for ${displayedTargets.length} targets started!`;
            $uiState.isScraping = true;
        } catch (error: any) {
            message = "Error starting scrape: " + error.message;
        } finally {
            isLoading = false;
        }
    }

    $: if (allTargets.length > 0) {
        if ($uiState.selectedScrapeTargetId) {
            displayedTargets = allTargets.filter(
                (t) => t.id === $uiState.selectedScrapeTargetId,
            );
            // Auto-focus on map
            const target = displayedTargets[0];
            if (target && target.latitude && target.longitude) {
                mapCenter = [target.latitude, target.longitude];
                mapBounds = null;
            }
        } else if ($uiState.selectedScrapeRegionId) {
            // This assumes objects in allTargets might have a region_id or similar.
            // If they don't, we might need to fetch them. For now, we clear or show all if untargeted.
            displayedTargets = allTargets;
        }
    }

    $: visibleTargetIds = displayedTargets.map((t) => t.id);
</script>

<div class="space-y-8">
    <!-- Map Section -->
    <div
        class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col gap-4"
    >
        <div
            class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4"
        >
            <h2
                class="text-2xl font-bold text-gray-800 flex items-center gap-2"
            >
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="h-7 w-7 text-blue-500"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                >
                    <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
                    />
                </svg>
                {$t("dashboard")}
            </h2>
            <div class="flex flex-wrap gap-2">
                <button
                    class="btn btn-sm btn-outline btn-primary"
                    on:click={resetView}
                >
                    {$t("reset_map")}
                </button>

                {#if $uiState.isScraping}
                    <button
                        class="btn btn-sm btn-error shadow-lg animate-pulse"
                        on:click={stopScrape}
                    >
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            class="h-4 w-4 mr-1"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                        >
                            <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                stroke-width="2"
                                d="M6 18L18 6M6 6l12 12"
                            />
                        </svg>
                        {$t("cancel_scrape")}
                    </button>
                {:else}
                    <button
                        class="btn btn-sm btn-primary shadow-lg"
                        on:click={scrapeVisible}
                        disabled={isLoading || displayedTargets.length === 0}
                    >
                        {#if isLoading}
                            <span class="loading loading-spinner loading-xs"
                            ></span>
                        {/if}
                        {$t("scrape_visible_targets")} ({displayedTargets.length})
                    </button>
                {/if}
            </div>
        </div>

        {#if message}
            <div class="alert alert-info py-3 mb-2 shadow-sm">
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    class="stroke-current shrink-0 w-6 h-6"
                    ><path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    ></path></svg
                >
                <span>{message}</span>
            </div>
        {/if}

        <div
            class="relative rounded-2xl overflow-hidden border border-gray-100 h-[400px] md:h-[500px] shadow-inner"
        >
            <Map
                targets={displayedTargets}
                viewCenter={mapCenter}
                bounds={mapBounds}
                on:focus={handleFocus}
            />
        </div>

        <div class="mt-2">
            <RadiusSearch on:searchcomplete={handleSearchComplete} />
        </div>
    </div>

    <!-- Results Section -->
    <div
        class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col gap-6"
    >
        <div
            class="flex items-center justify-between border-b border-gray-50 pb-4"
        >
            <h2
                class="text-2xl font-bold text-gray-800 flex items-center gap-3"
            >
                <div class="bg-green-100 p-2 rounded-lg">
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        class="h-6 w-6 text-green-600"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                        />
                    </svg>
                </div>
                {$t("results_for_selection")}
            </h2>
            <div class="badge badge-lg badge-ghost font-medium">
                {displayedTargets.length}
                {displayedTargets.length === 1 ? "Station" : "Stations"}
            </div>
        </div>

        <div class="min-h-[400px]">
            <ResultsViewer forcedTargetIds={visibleTargetIds} />
        </div>
    </div>
</div>
