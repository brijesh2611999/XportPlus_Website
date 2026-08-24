// const BaseScraper = require('./BaseScraper');
// const { saveToken } = require('../../config/db');

// class MscScraper extends BaseScraper {
//   constructor() {
//     super('MSC');
//     this.email = 'alejandro.delcarpio@primeteam.com.mx';
//     this.password = 'Adc19770123$';
//   }

//   async scrapeTokens() {
//     try {
//       console.log('Starting MSC scraper...');
//       await this.initBrowser();

//       let bearerToken = '';

//       await this.page.setRequestInterception(true);
//       this.page.on('request', (request) => {
//         const headers = request.headers();

//         if (request.url().includes('services.mymsc.com/quote/graphql') || request.url().includes('services.mymsc.com')) {
//           if (headers['authorization'] && headers['authorization'].startsWith('Bearer ')) {
//             bearerToken = headers['authorization'].split(' ')[1];
//           }
//         }
//         request.continue();
//       });

//       await this.page.goto('https://www.mymsc.com/', { waitUntil: 'networkidle2' });

//       // Handle cookies
//       try {
//         await this.page.waitForSelector('#onetrust-accept-btn-handler', { timeout: 3000 });
//         await this.page.click('#onetrust-accept-btn-handler');
//       } catch (e) {}

//       // Login
//       const isLoginVisible = await this.page.$('input[type="email"]');
//       if (isLoginVisible) {
//         console.log('Logging into MSC...');
//         await this.page.type('input[type="email"]', this.email);
//         await this.page.keyboard.press('Enter');

//         try {
//           await new Promise(r => setTimeout(r, 5000)); // hard wait for page transition
//           await this.page.waitForSelector('input[type="password"]', { timeout: 10000 });
//           await this.page.type('input[type="password"]', this.password);
//           await this.page.keyboard.press('Enter');

//           await this.page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 15000 }).catch(() => {});
//         } catch (err) {
//           console.log('Could not find password field or navigation failed:', err.message);
//         }
//       }

//       console.log('Waiting for tokens to be intercepted...');
//       await new Promise(r => setTimeout(r, 10000)); 

//       // Fallback: extract JWT token from anywhere in localStorage or sessionStorage
//       if (!bearerToken) {
//         bearerToken = await this.page.evaluate(() => {
//           let token = null;
//           // Look in localStorage
//           for (let i = 0; i < localStorage.length; i++) {
//             const key = localStorage.key(i);
//             const val = localStorage.getItem(key);
//             if (val && val.includes('eyJ') && val.length > 500) {
//               token = val;
//             }
//           }
//           // Look in sessionStorage
//           for (let i = 0; i < sessionStorage.length; i++) {
//             const key = sessionStorage.key(i);
//             const val = sessionStorage.getItem(key);
//             if (val && val.includes('eyJ') && val.length > 500) {
//               token = val;
//             }
//           }

//           // sometimes it's wrapped in JSON
//           if (token && token.startsWith('{')) {
//              try {
//                 const parsed = JSON.parse(token);
//                 if (parsed.secret) token = parsed.secret;
//                 else if (parsed.credential) token = parsed.credential;
//              } catch(e) {}
//           }
//           return token;
//         });
//       }

//       if (bearerToken) {
//         const tokenData = {
//           MSC_BEARER_TOKEN: bearerToken
//         };
//         await saveToken(this.siteName, tokenData);
//         console.log('MSC tokens saved to database.');
//       } else {
//         console.log('Failed to intercept MSC tokens. Taking screenshot...');
//         await this.page.screenshot({ path: 'msc_failed.png' });
//       }

//     } catch (error) {
//       console.error('Error during MSC scraping:', error);
//     } finally {
//       await this.closeBrowser();
//     }
//   }
// }

// module.exports = MscScraper;


// const BaseScraper = require('./BaseScraper');
// const { saveToken } = require('../config/db');

// class MscScraper extends BaseScraper {
//   constructor() {
//     super('MSC');
//     this.email = process.env.MSC_EMAIL;
//     this.password = process.env.MSC_PASSWORD;
//   }

//   async scrapeTokens() {
//     if (!this.email || !this.password) {
//       console.error('MSC_EMAIL / MSC_PASSWORD are not set — skipping MSC scrape.');
//       return;
//     }

//     try {
//       console.log('Starting MSC scraper...');
//       await this.initBrowser();

//       let bearerToken = '';

//       await this.page.setRequestInterception(true);
//       this.page.on('request', (request) => {
//         const headers = request.headers();
//         if (request.url().includes('services.mymsc.com')) {
//           if (headers['authorization'] && headers['authorization'].startsWith('Bearer ')) {
//             bearerToken = headers['authorization'].split(' ')[1];
//           }
//         }
//         request.continue();
//       });

//       await this.page.goto('https://www.mymsc.com/', { waitUntil: 'networkidle2' });

//       try {
//         await this.page.waitForSelector('#onetrust-accept-btn-handler', { timeout: 3000 });
//         await this.page.click('#onetrust-accept-btn-handler');
//       } catch (e) { }

//       const isLoginVisible = await this.page.$('input[type="email"]');
//       if (isLoginVisible) {
//         await this.page.type('input[type="email"]', this.email);
//         await this.page.keyboard.press('Enter');
//         try {
//           await new Promise(r => setTimeout(r, 5000));
//           await this.page.waitForSelector('input[type="password"]', { timeout: 10000 });
//           await this.page.type('input[type="password"]', this.password);
//           await this.page.keyboard.press('Enter');
//           await this.page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 15000 }).catch(() => { });
//         } catch (err) {
//           console.log('Could not find password field or navigation failed:', err.message);
//         }
//       }

//       await new Promise(r => setTimeout(r, 10000));

//       if (!bearerToken) {
//         bearerToken = await this.page.evaluate(() => {
//           let token = null;
//           for (let i = 0; i < localStorage.length; i++) {
//             const val = localStorage.getItem(localStorage.key(i));
//             if (val && val.includes('eyJ') && val.length > 500) token = val;
//           }
//           for (let i = 0; i < sessionStorage.length; i++) {
//             const val = sessionStorage.getItem(sessionStorage.key(i));
//             if (val && val.includes('eyJ') && val.length > 500) token = val;
//           }
//           if (token && token.startsWith('{')) {
//             try {
//               const parsed = JSON.parse(token);
//               if (parsed.secret) token = parsed.secret;
//               else if (parsed.credential) token = parsed.credential;
//             } catch (e) { }
//           }
//           return token;
//         });
//       }

//       if (bearerToken) {
//         await saveToken(this.siteName, { MSC_BEARER_TOKEN: bearerToken });
//         console.log('MSC tokens saved to database.');
//       } else {
//         console.log('Failed to intercept MSC tokens. Taking screenshot...');
//         await this.page.screenshot({ path: 'msc_failed.png' });
//       }
//     } catch (error) {
//       console.error('Error during MSC scraping:', error);
//     } finally {
//       await this.closeBrowser();
//     }
//   }
// }

// module.exports = MscScraper;


const BaseScraper = require('./BaseScraper');
const { saveToken } = require('../config/db');

class MscScraper extends BaseScraper {
  constructor() {
    super('MSC');
    this.email = process.env.MSC_EMAIL;
    this.password = process.env.MSC_PASSWORD;
  }

  async scrapeTokens() {
    if (!this.email || !this.password) {
      console.error('MSC_EMAIL / MSC_PASSWORD are not set — skipping MSC scrape.');
      return;
    }

    try {
      console.log('Starting MSC scraper...');
      await this.initBrowser();

      let bearerToken = '';

      await this.page.setRequestInterception(true);
      this.page.on('request', (request) => {
        const headers = request.headers();
        if (request.url().includes('services.mymsc.com')) {
          if (headers['authorization'] && headers['authorization'].startsWith('Bearer ')) {
            bearerToken = headers['authorization'].split(' ')[1];
          }
        }
        request.continue();
      });

      await this.page.goto('https://www.mymsc.com/', { waitUntil: 'networkidle2' });

      try {
        await this.page.waitForSelector('#onetrust-accept-btn-handler', { timeout: 3000 });
        await this.page.click('#onetrust-accept-btn-handler');
      } catch (e) { }

      const isLoginVisible = await this.page.$('input[type="email"]');
      if (isLoginVisible) {
        await this.page.type('input[type="email"]', this.email);
        await this.page.keyboard.press('Enter');
        try {
          await new Promise(r => setTimeout(r, 5000));
          await this.page.waitForSelector('input[type="password"]', { timeout: 10000 });
          await this.page.type('input[type="password"]', this.password);
          await this.page.keyboard.press('Enter');
          await this.page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 15000 }).catch(() => { });
        } catch (err) {
          console.log('Could not find password field or navigation failed:', err.message);
        }
      }

      await new Promise(r => setTimeout(r, 10000));

      if (!bearerToken) {
        bearerToken = await this.page.evaluate(() => {
          let token = null;
          for (let i = 0; i < localStorage.length; i++) {
            const val = localStorage.getItem(localStorage.key(i));
            if (val && val.includes('eyJ') && val.length > 500) token = val;
          }
          for (let i = 0; i < sessionStorage.length; i++) {
            const val = sessionStorage.getItem(sessionStorage.key(i));
            if (val && val.includes('eyJ') && val.length > 500) token = val;
          }
          if (token && token.startsWith('{')) {
            try {
              const parsed = JSON.parse(token);
              if (parsed.secret) token = parsed.secret;
              else if (parsed.credential) token = parsed.credential;
            } catch (e) { }
          }
          return token;
        });
      }

      if (bearerToken) {
        await saveToken(this.siteName, { MSC_BEARER_TOKEN: bearerToken });
        console.log('MSC tokens saved to database.');
      } else {
        console.log('Failed to intercept MSC tokens. Taking screenshot...');
        await this.page.screenshot({ path: 'msc_failed.png' });
      }
    } catch (error) {
      console.error('Error during MSC scraping:', error);
    } finally {
      await this.closeBrowser();
    }
  }
}

module.exports = MscScraper;