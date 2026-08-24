// const app = require('./app');
// const config = require('./config/config');
// const { initDB } = require('./config/db');
// const { startCronJob } = require('./services/cronService');

// const startServer = async () => {
//     // Initialize Database
//     await initDB();

//     // Start Token Scraper Cron Job
//     startCronJob();

//     // Start Express Server
//     app.listen(config.PORT, () => {
//         console.log(`✅ Server is running in ${process.env.NODE_ENV || 'development'} mode on http://localhost:${config.PORT}`);
//     });
// };

// startServer();
const app = require('./app');
const config = require('./config/config');
const { initDB } = require('./config/db');
const { startCronJob } = require('./services/cronService');

const startServer = async () => {
    await initDB();
    startCronJob();
    app.listen(config.PORT, () => {
        console.log(`Server running on http://localhost:${config.PORT}`);
    });
};

startServer();