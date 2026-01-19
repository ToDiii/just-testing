import { writable, derived } from 'svelte/store';

// UI State Store
export const uiState = writable({
    filterRegionId: null as number | null,
    selectedScrapeRegionId: null as number | null,
    selectedScrapeTargetId: null as number | null,
    logs: [] as string[],
    showLogs: false,
    filterSearch: '',
    isScraping: false
});

// Internationalization (I18n) Store
export type Language = 'de' | 'en';
export const language = writable<Language>('de');

interface Translations {
    [key: string]: {
        [lang in Language]: string;
    };
}

const translations: Translations = {
    'app_title': { de: 'Scraper Dashboard', en: 'Scraper Dashboard' },
    'map': { de: 'Karte', en: 'Map' },
    'results': { de: 'Ergebnisse', en: 'Results' },
    'manage_targets': { de: 'Ziele verwalten', en: 'Manage Targets' },
    'admin': { de: 'Admin', en: 'Admin' },
    'scraping_in_progress': { de: 'Scraping läuft...', en: 'Scraping in progress...' },
    'scrape_control_center': { de: 'Scrape Kontrollzentrum', en: 'Scrape Control Center' },
    'launch_targeted_scans': { de: 'Gezielte Scans starten und Fortschritt überwachen', en: 'Launch targeted scans and monitor progress' },
    'start_scrape': { de: 'SCRAPING STARTEN', en: 'START SCRAPE' },
    'region': { de: 'Region', en: 'Region' },
    'municipality': { de: 'Kommune', en: 'Municipality' },
    'all_regions': { de: 'Alle Regionen', en: 'All Regions' },
    'all_targets': { de: 'Alle Ziele (Regionsbasiert)', en: 'All Targets (Region based)' },
    'filter_by_keyword': { de: 'Nach Stichwort filtern...', en: 'Filter by keyword...' },
    'view_all_regions': { de: 'Alle Regionen anzeigen', en: 'View All Regions' },
    'view_engine_logs': { de: 'Engine Logs anzeigen', en: 'View Engine Logs' },
    'hide_logs': { de: 'Logs ausblenden', en: 'Hide Logs' },
    'clear_console': { de: 'Konsole leeren', en: 'Clear Console' },
    'no_logs_recorded': { de: '-- ENDE DES LOG-STREAMS -- (Keine Aktivitäten im Puffer)', en: '-- END_OF_LOG_STREAM -- (No activities recorded in current buffer)' },
    'engine_active': { de: '>> ENGINE AKTIV: Neue Daten-Chunks abfragen...', en: '>> ENGINE_ACTIVE: Polling new data chunks...' },
    'initializing_scraper': { de: 'Initialisiere Scraper... warte auf erste Daten...', en: 'Initializing scraper... awaiting first data...' },
    'loading_results': { de: 'Lade Ergebnisse...', en: 'Loading results...' },
    'no_results_found': { de: 'Keine Ergebnisse gefunden. Versuche einen Scrape zu starten.', en: 'No results found. Try running a scrape.' },
    'title': { de: 'Titel', en: 'Title' },
    'source': { de: 'Quelle', en: 'Source' },
    'publication_date': { de: 'Veröffentlichungsdatum', en: 'Publication Date' },
    'scraped_at': { de: 'Gescrappt am', en: 'Scraped At' },
    'active': { de: 'Aktiv', en: 'Active' },
    'manage_targets_keywords': { de: 'Ziele & Stichworte verwalten', en: 'Manage Targets & Keywords' },
    'add_target': { de: 'Ziel hinzufügen', en: 'Add Target' },
    'existing_targets': { de: 'Vorhandene Ziele', en: 'Existing Targets' },
    'scrape_all_targets': { de: 'Alle Ziele scrappen', en: 'Scrape All Targets' },
    'last_scrape_started': { de: 'Letzter Scrape gestartet', en: 'Last scrape started' },
    'last_scrape_finished': { de: 'Letzter Scrape beendet', en: 'Last scrape finished' },
    'filter_targets': { de: 'Ziele filtern...', en: 'Filter targets...' },
    'loading_targets': { de: 'Lade Ziele...', en: 'Loading targets...' },
    'no_targets_configured': { de: 'Noch keine Ziele konfiguriert.', en: 'No targets configured yet.' },
    'no_targets_match': { de: 'Keine Ziele entsprechen deinem Filter.', en: 'No targets match your filter.' },
    'name': { de: 'Name', en: 'Name' },
    'url': { de: 'URL', en: 'URL' },
    'last_scraped': { de: 'Zuletzt gescrappt', en: 'Last Scraped' },
    'select_region_optional': { de: 'Region auswählen (Optional)', en: 'Select Region (Optional)' },
    'admin_dashboard': { de: 'Admin Dashboard', en: 'Admin Dashboard' },
    'scraping_limits': { de: 'Scraping-Limits', en: 'Scraping Limits' },
    'max_html_links': { de: 'Max. HTML Links', en: 'Max HTML Links' },
    'max_pdf_links': { de: 'Max. PDF Links', en: 'Max PDF Links' },
    'request_delay': { de: 'Abfrage-Verzögerung (s)', en: 'Request Delay (s)' },
    'save_limits': { de: 'Limits speichern', en: 'Save Limits' },
    'notification_channels': { de: 'Benachrichtigungskanäle', en: 'Notification Channels' },
    'add_new_channel': { de: 'Neuen Kanal hinzufügen', en: 'Add New Channel' },
    'webhook': { de: 'Webhook', en: 'Webhook' },
    'email': { de: 'E-Mail', en: 'Email' },
    'recipient': { de: 'Empfänger', en: 'Recipient' },
    'add': { de: 'Hinzufügen', en: 'Add' },
    'delete': { de: 'Löschen', en: 'Delete' },
    'test': { de: 'Testen', en: 'Test' },
    'enabled': { de: 'Aktiviert', en: 'Enabled' },
    'disabled': { de: 'Deaktiviert', en: 'Disabled' },
    'keywords': { de: 'Stichworte', en: 'Keywords' },
    'categories': { de: 'Kategorien', en: 'Categories' },
    'add_keyword': { de: 'Stichwort hinzufügen', en: 'Add Keyword' },
    'add_category': { de: 'Kategorie hinzufügen', en: 'Add Category' },
    'select_category': { de: 'Kategorie wählen', en: 'Select Category' },
    'keyword_placeholder': { de: 'Stichwort...', en: 'Keyword...' },
    'category_placeholder': { de: 'Kategoriename...', en: 'Category name...' },
    'never': { de: 'Niemals', en: 'Never' },
    'ago': { de: 'vor', en: 'ago' },
    'dashboard': { de: 'Dashboard', en: 'Dashboard' },
    'scrape_visible_targets': { de: 'Sichtbare Ziele abfragen', en: 'Scrape visible targets' },
    'results_for_selection': { de: 'Ergebnisse für aktuelle Auswahl', en: 'Results for current selection' },
    'reset_map': { de: 'Karte zurücksetzen', en: 'Reset Map' },
    'focus_on_target': { de: 'Ziel fokussieren', en: 'Focus on target' },
    'search_by_radius': { de: 'Umkreissuche', en: 'Radius Search' },
    'enter_address': { de: 'Adresse oder Stadt eingeben', en: 'Enter an address or city' },
    'search': { de: 'Suchen', en: 'Search' },
    'locate_me': { de: 'Meinen Standort finden', en: 'Locate me' },
    'cancel_scrape': { de: 'Abbrechen', en: 'Cancel' },
    'use_my_location': { de: 'Meinen Standort verwenden', en: 'Use my location' },
};

export const t = derived(language, ($lang) => {
    return (key: string) => translations[key]?.[$lang] || key;
});
