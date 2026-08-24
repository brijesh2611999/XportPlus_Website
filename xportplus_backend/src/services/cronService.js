// const cron = require('node-cron');
// const CmaScraper = require('./scraper/CmaScraper');
// const MscScraper = require('./scraper/MscScraper');

// const runScrapers = async () => {
//   console.log('Running automated scrapers to fetch fresh tokens...');

//   const cmaScraper = new CmaScraper();
//   await cmaScraper.scrapeTokens();

//   const mscScraper = new MscScraper();
//   await mscScraper.scrapeTokens();

//   console.log('Scraping cycle complete.');
// };

// // Start the cron job to run every 12 minutes
// const startCronJob = () => {
//   // '*/12 * * * *' means every 12 minutes
//   cron.schedule('*/12 * * * *', async () => {
//     try {
//       await runScrapers();
//     } catch (err) {
//       console.error('Error in cron job:', err);
//     }
//   });
//   console.log('Token scraper cron job scheduled (every 12 minutes).');

//   // Also run once immediately on startup
//   setTimeout(runScrapers, 2000);
// };

// module.exports = {
//   startCronJob,
//   runScrapers
// };

const cron = require('node-cron');
const CmaScraper = require('../scraper/CmaScraper');
const MscScraper = require('../scraper/MscScraper');
const scraperLock = require('./scraperLock');

scraperLock.registerScraper('CMA-CGM', () => new CmaScraper());
scraperLock.registerScraper('MSC', () => new MscScraper());

const runScrapers = async () => {
  console.log('Running automated scrapers to fetch fresh tokens...');
  const results = await Promise.allSettled([
    scraperLock.refreshSite('CMA-CGM'),
    scraperLock.refreshSite('MSC'),
  ]);
  results.forEach((result, i) => {
    const site = i === 0 ? 'CMA-CGM' : 'MSC';
    if (result.status === 'rejected') console.error(`Scrape failed for ${site}:`, result.reason);
  });
  console.log('Scraping cycle complete.');
};

const startCronJob = () => {
  cron.schedule('*/12 * * * *', async () => {
    try {
      await runScrapers();
    } catch (err) {
      console.error('Error in cron job:', err);
    }
  });
  console.log('Token scraper cron job scheduled (every 12 minutes).');
  setTimeout(runScrapers, 2000);
};

module.exports = { startCronJob, runScrapers };