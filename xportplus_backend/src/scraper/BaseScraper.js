// const puppeteer = require('puppeteer-extra');
// const StealthPlugin = require('puppeteer-extra-plugin-stealth');
// puppeteer.use(StealthPlugin());

// class BaseScraper {
//   constructor(siteName) {
//     this.siteName = siteName;
//     this.browser = null;
//     this.page = null;
//   }

//   async initBrowser() {
//     this.browser = await puppeteer.launch({
//       headless: false,
//       args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-blink-features=AutomationControlled']
//     });
//     this.page = await this.browser.newPage();
//     await this.page.setViewport({ width: 1280, height: 800 });
//   }

//   async closeBrowser() {
//     if (this.browser) {
//       await this.browser.close();
//       this.browser = null;
//       this.page = null;
//     }
//   }

//   // To be implemented by subclasses
//   async scrapeTokens() {
//     throw new Error('scrapeTokens must be implemented by subclass');
//   }
// }

// module.exports = BaseScraper;
// const puppeteer = require('puppeteer-extra');
// const StealthPlugin = require('puppeteer-extra-plugin-stealth');
// puppeteer.use(StealthPlugin());

// const resolveHeadless = () => {
//   const val = process.env.SCRAPER_HEADLESS || 'new';
//   if (val === 'false') return false;
//   if (val === 'true') return true;
//   return val;
// };

// class BaseScraper {
//   constructor(siteName) {
//     this.siteName = siteName;
//     this.browser = null;
//     this.page = null;
//   }

//   async initBrowser() {
//     this.browser = await puppeteer.launch({
//       headless: resolveHeadless(),
//       args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-blink-features=AutomationControlled'],
//     });
//     this.page = await this.browser.newPage();
//     await this.page.setViewport({ width: 1280, height: 800 });
//   }

//   async closeBrowser() {
//     if (this.browser) {
//       await this.browser.close();
//       this.browser = null;
//       this.page = null;
//     }
//   }

//   async scrapeTokens() {
//     throw new Error('scrapeTokens must be implemented by subclass');
//   }
// }

// module.exports = BaseScraper;



const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

const resolveHeadless = () => {
  const val = process.env.SCRAPER_HEADLESS || 'new';
  if (val === 'false') return false;
  if (val === 'true') return true;
  return val;
};

class BaseScraper {
  constructor(siteName) {
    this.siteName = siteName;
    this.browser = null;
    this.page = null;
  }

  async initBrowser() {
    this.browser = await puppeteer.launch({
      headless: resolveHeadless(),
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-blink-features=AutomationControlled'],
    });
    this.page = await this.browser.newPage();
    await this.page.setViewport({ width: 1280, height: 800 });
  }

  async closeBrowser() {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
      this.page = null;
    }
  }

  async scrapeTokens() {
    throw new Error('scrapeTokens must be implemented by subclass');
  }
}

module.exports = BaseScraper;