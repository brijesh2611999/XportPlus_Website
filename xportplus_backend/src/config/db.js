// const { Pool } = require('pg');
// require('dotenv').config();

// const pool = new Pool({
//   connectionString: process.env.DATABASE_URL || 'postgres://postgres:postgres@localhost:5432/xportplus',
// });

// // Initialize the database table for tokens
// const initDB = async () => {
//   try {
//     const createTableQuery = `
//       CREATE TABLE IF NOT EXISTS site_tokens (
//         site_name VARCHAR(50) PRIMARY KEY,
//         token_data JSONB NOT NULL,
//         last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
//       );
//     `;
//     await pool.query(createTableQuery);
//     console.log('Database connected and tokens table initialized.');
//   } catch (err) {
//     console.error('Error initializing database:', err);
//   }
// };

// const getToken = async (siteName) => {
//   try {
//     const res = await pool.query('SELECT token_data FROM site_tokens WHERE site_name = $1', [siteName]);
//     if (res.rows.length > 0) {
//       return res.rows[0].token_data;
//     }
//     return null;
//   } catch (err) {
//     console.error(`Error getting token for ${siteName}:`, err);
//     return null;
//   }
// };

// const saveToken = async (siteName, tokenData) => {
//   try {
//     const upsertQuery = `
//       INSERT INTO site_tokens (site_name, token_data, last_updated)
//       VALUES ($1, $2, CURRENT_TIMESTAMP)
//       ON CONFLICT (site_name)
//       DO UPDATE SET token_data = EXCLUDED.token_data, last_updated = CURRENT_TIMESTAMP;
//     `;
//     await pool.query(upsertQuery, [siteName, tokenData]);
//     console.log(`Successfully saved new tokens for ${siteName} in DB.`);
//   } catch (err) {
//     console.error(`Error saving token for ${siteName}:`, err);
//   }
// };

// module.exports = {
//   pool,
//   initDB,
//   getToken,
//   saveToken
// };


const { Pool } = require('pg');
require('dotenv').config();

const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgres://postgres:postgres@localhost:5432/xportplus',
});

const TOKEN_TTL_MINUTES = parseInt(process.env.TOKEN_TTL_MINUTES || '12', 10);

const initDB = async () => {
  try {
    await pool.query(`
      CREATE TABLE IF NOT EXISTS site_tokens (
        site_name VARCHAR(50) PRIMARY KEY,
        token_data JSONB NOT NULL,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    `);
    console.log('Database connected and tokens table initialized.');
  } catch (err) {
    console.error('Error initializing database:', err);
  }
};

const getToken = async (siteName) => {
  try {
    const res = await pool.query('SELECT token_data FROM site_tokens WHERE site_name = $1', [siteName]);
    return res.rows.length > 0 ? res.rows[0].token_data : null;
  } catch (err) {
    console.error(`Error getting token for ${siteName}:`, err);
    return null;
  }
};

const getTokenWithMeta = async (siteName) => {
  try {
    const res = await pool.query(
      'SELECT token_data, last_updated FROM site_tokens WHERE site_name = $1',
      [siteName]
    );
    if (res.rows.length === 0) return { tokenData: null, isFresh: false, lastUpdated: null };
    const { token_data, last_updated } = res.rows[0];
    const ageMinutes = (Date.now() - new Date(last_updated).getTime()) / 60000;
    return { tokenData: token_data, isFresh: ageMinutes < TOKEN_TTL_MINUTES, lastUpdated: last_updated };
  } catch (err) {
    console.error(`Error getting token metadata for ${siteName}:`, err);
    return { tokenData: null, isFresh: false, lastUpdated: null };
  }
};

const saveToken = async (siteName, tokenData) => {
  try {
    await pool.query(`
      INSERT INTO site_tokens (site_name, token_data, last_updated)
      VALUES ($1, $2, CURRENT_TIMESTAMP)
      ON CONFLICT (site_name)
      DO UPDATE SET token_data = EXCLUDED.token_data, last_updated = CURRENT_TIMESTAMP;
    `, [siteName, tokenData]);
    console.log(`Successfully saved new tokens for ${siteName} in DB.`);
  } catch (err) {
    console.error(`Error saving token for ${siteName}:`, err);
  }
};

module.exports = { pool, initDB, getToken, getTokenWithMeta, saveToken };