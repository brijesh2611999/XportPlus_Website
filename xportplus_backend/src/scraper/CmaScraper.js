// const BaseScraper = require('./BaseScraper');
// const { saveToken } = require('../../config/db');

// class CmaScraper extends BaseScraper {
//   constructor() {
//     super('CMA-CGM');
//     this.email = 'Alejandro.delcarpio@primeteam.com.mx';
//     this.password = 'Prime123$';
//   }

//   async scrapeTokens() {
//     try {
//       console.log('Starting CMA-CGM scraper...');
//       await this.initBrowser();

//       let cookieString = '';
//       let xsrfToken = '';

//       // Intercept network requests to capture headers
//       await this.page.setRequestInterception(true);
//       this.page.on('request', (request) => {
//         const headers = request.headers();

//         // Grab the tokens from API calls once logged in
//         if (request.url().includes('/apigw/commercial/spoton/bff/v1/')) {
//           if (headers['cookie']) {
//             cookieString = headers['cookie'];
//           }
//           if (headers['x-csrf-token']) {
//             xsrfToken = headers['x-csrf-token'];
//           }
//         }
//         request.continue();
//       });

//       const loginUrl = "https://auth.cma-cgm.com/as/authorization.oauth2?client_id=webapp-must&redirect_uri=https%3A%2F%2Fwww.cma-cgm.com%2Fsignin-oidc&response_type=code&scope=email%20openid%20profile%20Ecom%3Awebapp-must-apl-anl-cnc%20ans%3Afe%3Aread%20ans%3Afe%3Awrite&code_challenge=ET8OZSyeprUtfKR_RN0Cs6zDttj4A7iqt45JRhUlTyI&code_challenge_method=S256&response_mode=form_post&state=CfDJ8NkZuqwa3GhPsRXnBVeIDCZyJiiF_HuP1tfJK3_JU9Wk_crDfdawtoCxizQGaJQWO1bWeLXvku7HjEmVOoURFlIOqrI39qE5lmb3IfHdADPzIZht3uPQ_yN6JcOkLvcYQKH7YVFNsGpqOnJqyIEgXum_sLX32FjQen-1wKve-1UzLNUwCdJldIhtsLLvKMXZN49Msbf8l9ZXpUt5ZnQgow6K-hQn_mYtw4xVP7WPFAAHVLhEA4iqpGCOFzM377BlxeRcWXC64kB7NeE3SVrtXUSNGXtPtgPJw-aQbnK31LOG4_JBgXjsv-8mSXu5K1kSXu-JKr6WYL4-padURNoVHI9te5DM3bUEmmoHr3jaoDVrz4uwYPT4kkH0wzdn7Nj4bpIf9kqMWwVb3LFZg_Qdbxjvx0vOi7Ti9KL7YtjecnYjG4QVECyVyhecOQOKeI7fp9_O2rgulGgbZoCVsFb05rw&Language=en-US&actas=false&x-client-SKU=ID_NET8_0&x-client-ver=7.4.1.0";

//       await this.page.goto(loginUrl, { waitUntil: 'networkidle2' });

//       try {
//         await this.page.waitForSelector('#onetrust-accept-btn-handler', { timeout: 3000 });
//         await this.page.click('#onetrust-accept-btn-handler');
//       } catch (e) {}

//       console.log('Checking for login form...');
//       // Wait for PingIdentity username field
//       try {
//         await this.page.waitForSelector('input[name="pf.username"], input[type="email"], #username', { timeout: 10000 });
//         console.log('Logging into CMA-CGM...');

//         // Use generic selectors that work on PingIdentity / OIDC
//         await this.page.type('input[name="pf.username"], input[type="email"], #username', this.email);
//         await this.page.type('input[name="pf.pass"], input[type="password"], #password', this.password);

//         await this.page.evaluate(() => {
//           const btn = document.querySelector('button[type="submit"], input[type="submit"], a.button');
//           if (btn) btn.click();
//         });

//         await this.page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 15000 }).catch(() => {});
//       } catch (err) {
//         console.log('Login form not found or already logged in:', err.message);
//       }// Trigger a network request by interacting with the page, or just wait if it automatically fetches data
//       console.log('Waiting for tokens to be intercepted...');
//       await new Promise(r => setTimeout(r, 10000)); // Wait 10 seconds for interception to catch the API calls

//       if (cookieString && xsrfToken) {
//         const tokenData = {
//           CMA_COOKIE: cookieString,
//           CMA_XSRF_TOKEN: xsrfToken
//         };
//         await saveToken(this.siteName, tokenData);
//         console.log('CMA-CGM tokens saved to database.');
//       } else {
//         console.log('Failed to intercept CMA-CGM tokens. Taking screenshot...');
//         await this.page.screenshot({ path: 'cma_failed.png' });
//       }

//     } catch (error) {
//       console.error('Error during CMA-CGM scraping:', error);
//     } finally {
//       await this.closeBrowser();
//     }
//   }
// }

// module.exports = CmaScraper;



// const BaseScraper = require('./BaseScraper');
// const { saveToken } = require('../config/db');

// class CmaScraper extends BaseScraper {
//   constructor() {
//     super('CMA-CGM');
//     this.email = process.env.CMA_EMAIL;
//     this.password = process.env.CMA_PASSWORD;
//   }

//   async scrapeTokens() {
//     if (!this.email || !this.password) {
//       console.error('CMA_EMAIL / CMA_PASSWORD are not set — skipping CMA scrape.');
//       return;
//     }

//     try {
//       console.log('Starting CMA-CGM scraper...');
//       await this.initBrowser();

//       let cookieString = '';
//       let xsrfToken = '';

//       await this.page.setRequestInterception(true);
//       this.page.on('request', (request) => {
//         const headers = request.headers();
//         if (request.url().includes('/apigw/commercial/spoton/bff/v1/')) {
//           if (headers['cookie']) cookieString = headers['cookie'];
//           if (headers['x-csrf-token']) xsrfToken = headers['x-csrf-token'];
//         }
//         request.continue();
//       });

//       const loginUrl = "https://auth.cma-cgm.com/as/authorization.oauth2?client_id=webapp-must&redirect_uri=https%3A%2F%2Fwww.cma-cgm.com%2Fsignin-oidc&response_type=code&scope=email%20openid%20profile%20Ecom%3Awebapp-must-apl-anl-cnc%20ans%3Afe%3Aread%20ans%3Afe%3Awrite&code_challenge=ET8OZSyeprUtfKR_RN0Cs6zDttj4A7iqt45JRhUlTyI&code_challenge_method=S256&response_mode=form_post&state=CfDJ8NkZuqwa3GhPsRXnBVeIDCZyJiiF_HuP1tfJK3_JU9Wk_crDfdawtoCxizQGaJQWO1bWeLXvku7HjEmVOoURFlIOqrI39qE5lmb3IfHdADPzIZht3uPQ_yN6JcOkLvcYQKH7YVFNsGpqOnJqyIEgXum_sLX32FjQen-1wKve-1UzLNUwCdJldIhtsLLvKMXZN49Msbf8l9ZXpUt5ZnQgow6K-hQn_mYtw4xVP7WPFAAHVLhEA4iqpGCOFzM377BlxeRcWXC64kB7NeE3SVrtXUSNGXtPtgPJw-aQbnK31LOG4_JBgXjsv-8mSXu5K1kSXu-JKr6WYL4-padURNoVHI9te5DM3bUEmmoHr3jaoDVrz4uwYPT4kkH0wzdn7Nj4bpIf9kqMWwVb3LFZg_Qdbxjvx0vOi7Ti9KL7YtjecnYjG4QVECyVyhecOQOKeI7fp9_O2rgulGgbZoCVsFb05rw&Language=en-US&actas=false&x-client-SKU=ID_NET8_0&x-client-ver=7.4.1.0";

//       await this.page.goto(loginUrl, { waitUntil: 'networkidle2' });

//       try {
//         await this.page.waitForSelector('#onetrust-accept-btn-handler', { timeout: 3000 });
//         await this.page.click('#onetrust-accept-btn-handler');
//       } catch (e) { }

//       try {
//         await this.page.waitForSelector('input[name="pf.username"], input[type="email"], #username', { timeout: 10000 });
//         await this.page.type('input[name="pf.username"], input[type="email"], #username', this.email);
//         await this.page.type('input[name="pf.pass"], input[type="password"], #password', this.password);
//         await this.page.evaluate(() => {
//           const btn = document.querySelector('button[type="submit"], input[type="submit"], a.button');
//           if (btn) btn.click();
//         });
//         await this.page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 15000 }).catch(() => { });
//       } catch (err) {
//         console.log('Login form not found or already logged in:', err.message);
//       }

//       await new Promise(r => setTimeout(r, 10000));

//       if (cookieString && xsrfToken) {
//         await saveToken(this.siteName, { CMA_COOKIE: cookieString, CMA_XSRF_TOKEN: xsrfToken });
//         console.log('CMA-CGM tokens saved to database.');
//       } else {
//         console.log('Failed to intercept CMA-CGM tokens. Taking screenshot...');
//         await this.page.screenshot({ path: 'cma_failed.png' });
//       }
//     } catch (error) {
//       console.error('Error during CMA-CGM scraping:', error);
//     } finally {
//       await this.closeBrowser();
//     }
//   }
// }

// module.exports = CmaScraper;

const BaseScraper = require('./BaseScraper');
const { saveToken } = require('../config/db');

class CmaScraper extends BaseScraper {
  constructor() {
    super('CMA-CGM');
    this.email = process.env.CMA_EMAIL;
    this.password = process.env.CMA_PASSWORD;
  }

  async scrapeTokens() {
    if (!this.email || !this.password) {
      console.error('CMA_EMAIL / CMA_PASSWORD are not set — skipping CMA scrape.');
      return;
    }

    try {
      console.log('Starting CMA-CGM scraper...');
      await this.initBrowser();

      let cookieString = '';
      let xsrfToken = '';

      await this.page.setRequestInterception(true);
      this.page.on('request', (request) => {
        const headers = request.headers();
        if (request.url().includes('/apigw/commercial/spoton/bff/v1/')) {
          if (headers['cookie']) cookieString = headers['cookie'];
          if (headers['x-csrf-token']) xsrfToken = headers['x-csrf-token'];
        }
        request.continue();
      });

      const loginUrl = "https://auth.cma-cgm.com/as/authorization.oauth2?client_id=webapp-must&redirect_uri=https%3A%2F%2Fwww.cma-cgm.com%2Fsignin-oidc&response_type=code&scope=email%20openid%20profile%20Ecom%3Awebapp-must-apl-anl-cnc%20ans%3Afe%3Aread%20ans%3Afe%3Awrite&code_challenge=ET8OZSyeprUtfKR_RN0Cs6zDttj4A7iqt45JRhUlTyI&code_challenge_method=S256&response_mode=form_post&state=CfDJ8NkZuqwa3GhPsRXnBVeIDCZyJiiF_HuP1tfJK3_JU9Wk_crDfdawtoCxizQGaJQWO1bWeLXvku7HjEmVOoURFlIOqrI39qE5lmb3IfHdADPzIZht3uPQ_yN6JcOkLvcYQKH7YVFNsGpqOnJqyIEgXum_sLX32FjQen-1wKve-1UzLNUwCdJldIhtsLLvKMXZN49Msbf8l9ZXpUt5ZnQgow6K-hQn_mYtw4xVP7WPFAAHVLhEA4iqpGCOFzM377BlxeRcWXC64kB7NeE3SVrtXUSNGXtPtgPJw-aQbnK31LOG4_JBgXjsv-8mSXu5K1kSXu-JKr6WYL4-padURNoVHI9te5DM3bUEmmoHr3jaoDVrz4uwYPT4kkH0wzdn7Nj4bpIf9kqMWwVb3LFZg_Qdbxjvx0vOi7Ti9KL7YtjecnYjG4QVECyVyhecOQOKeI7fp9_O2rgulGgbZoCVsFb05rw&Language=en-US&actas=false&x-client-SKU=ID_NET8_0&x-client-ver=7.4.1.0";

      await this.page.goto(loginUrl, { waitUntil: 'networkidle2' });

      try {
        await this.page.waitForSelector('#onetrust-accept-btn-handler', { timeout: 3000 });
        await this.page.click('#onetrust-accept-btn-handler');
      } catch (e) { }

      try {
        await this.page.waitForSelector('input[name="pf.username"], input[type="email"], #username', { timeout: 10000 });
        await this.page.type('input[name="pf.username"], input[type="email"], #username', this.email);
        await this.page.type('input[name="pf.pass"], input[type="password"], #password', this.password);
        await this.page.evaluate(() => {
          const btn = document.querySelector('button[type="submit"], input[type="submit"], a.button');
          if (btn) btn.click();
        });
        await this.page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 15000 }).catch(() => { });
      } catch (err) {
        console.log('Login form not found or already logged in:', err.message);
      }

      await new Promise(r => setTimeout(r, 10000));

      if (cookieString && xsrfToken) {
        await saveToken(this.siteName, { CMA_COOKIE: cookieString, CMA_XSRF_TOKEN: xsrfToken });
        console.log('CMA-CGM tokens saved to database.');
      } else {
        console.log('Failed to intercept CMA-CGM tokens. Taking screenshot...');
        await this.page.screenshot({ path: 'cma_failed.png' });
      }
    } catch (error) {
      console.error('Error during CMA-CGM scraping:', error);
    } finally {
      await this.closeBrowser();
    }
  }
}

module.exports = CmaScraper;