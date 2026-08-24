const inFlight = new Map();
const scraperFactories = {};

const registerScraper = (siteName, factory) => {
    scraperFactories[siteName] = factory;
};

const refreshSite = async (siteName) => {
    if (inFlight.has(siteName)) return inFlight.get(siteName);

    const factory = scraperFactories[siteName];
    if (!factory) throw new Error(`No scraper registered for site "${siteName}"`);

    const runPromise = (async () => {
        try {
            const scraper = factory();
            await scraper.scrapeTokens();
        } finally {
            inFlight.delete(siteName);
        }
    })();

    inFlight.set(siteName, runPromise);
    return runPromise;
};

const isRefreshing = (siteName) => inFlight.has(siteName);

module.exports = { registerScraper, refreshSite, isRefreshing };