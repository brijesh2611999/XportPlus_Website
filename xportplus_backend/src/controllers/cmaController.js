// const axios = require('axios');
// const { getToken } = require('../config/db');
// require('dotenv').config();

// const getCmaQuotes = async (req, res) => {
//     try {
//         const payload = req.body;

//         // Fetch active tokens from DB
//         const tokenData = await getToken('CMA-CGM');
//         if (!tokenData || !tokenData.CMA_COOKIE || !tokenData.CMA_XSRF_TOKEN) {
//              throw new Error('CMA-CGM tokens are missing or expired in the database.');
//         }

//         // Setup initial headers for CMA CGM API
//         const headers = {
//             'accept': 'application/json, text/plain, */*',
//             'accept-language': 'en-US,en;q=0.9',
//             'content-type': 'application/json',
//             'cookie': tokenData.CMA_COOKIE,
//             'origin': 'https://www.cma-cgm.com',
//             'referer': 'https://www.cma-cgm.com/ebusiness/pricing/instant-Quoting',
//             'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
//             'x-csrf-token': tokenData.CMA_XSRF_TOKEN,
//             'x-requested-with': 'XMLHttpRequest'
//         };

//         // 1. Fetch initial best offer
//         const bestOfferResponse = await axios.post(
//             'https://www.cma-cgm.com/apigw/commercial/spoton/bff/v1/getbestoffer',
//             payload,
//             { headers }
//         );

//         if (!bestOfferResponse.data || !bestOfferResponse.data.QuoteLineAndRoutingHeaders) {
//             return res.status(400).json({ success: false, message: 'No quotes found or invalid response' });
//         }

//         const quotes = bestOfferResponse.data.QuoteLineAndRoutingHeaders;
//         const finalResults = [];

//         // 2. Loop through each quote and fetch allocation details
//         // We do this sequentially to avoid overwhelming the server/triggering anti-bot,
//         // but Promise.all could be used if speed is paramount and bans aren't an issue.
//         for (const quote of quotes) {
//             const nextDepartureIndex = quote.NextDepartureIndex;
//             if (!nextDepartureIndex) continue;

//             try {
//                 const detailsResponse = await axios.get(
//                     `https://www.cma-cgm.com/apigw/commercial/spoton/bff/v1/allocationandchargedetails/${nextDepartureIndex}`,
//                     { headers }
//                 );

//                 // Extract only Price and Date as requested
//                 // Note: The specific structure of detailsResponse might require adjusting this extraction logic 
//                 // once we see the actual API response for allocation details.
//                 const departureDate = quote.DepartureDate;
//                 const arrivalDate = quote.ArrivalDate;

//                 // Extract precise prices from the secondary allocation and charge details API
//                 const cargoDetails = detailsResponse.data?.CargoChargeDetails || [];
//                 const prices = cargoDetails.map(charge => ({
//                     equipmentType: charge.EquipmentSizeType,
//                     oceanFreight: charge.OceanFreight?.Rate,
//                     totalCharge: charge.TotalCharge?.Rate,
//                     currency: charge.TotalCharge?.CurrencyCode || 'USD'
//                 }));

//                 finalResults.push({
//                     scheduleId: nextDepartureIndex,
//                     departureDate,
//                     arrivalDate,
//                     transitTime: quote.TransitTime,
//                     vesselName: quote.VesselName,
//                     prices: prices
//                 });

//             } catch (detailError) {
//                 console.error(`Failed to fetch details for index ${nextDepartureIndex}:`, detailError.message);
//                 // Continue to next quote even if one fails
//             }
//         }

//         res.json({
//             success: true,
//             data: finalResults
//         });

//     } catch (error) {
//         console.error('Error fetching CMA quotes:', error.response ? error.response.data : error.message);
//         res.status(500).json({ 
//             success: false, 
//             message: 'Failed to fetch CMA quotes', 
//             error: error.response ? error.response.status : error.message 
//         });
//     }
// };

// module.exports = {
//     getCmaQuotes
// };
const axios = require('axios');
const { getTokenWithMeta } = require('../config/db');
const scraperLock = require('../services/scraperLock');
require('dotenv').config();

const SITE_NAME = 'CMA-CGM';

const buildHeaders = (tokenData) => ({
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/json',
    'cookie': tokenData.CMA_COOKIE,
    'origin': 'https://www.cma-cgm.com',
    'referer': 'https://www.cma-cgm.com/ebusiness/pricing/instant-Quoting',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
    'x-csrf-token': tokenData.CMA_XSRF_TOKEN,
    'x-requested-with': 'XMLHttpRequest',
});

const fetchQuotesWithToken = async (tokenData, payload) => {
    const headers = buildHeaders(tokenData);
    const bestOfferResponse = await axios.post(
        'https://www.cma-cgm.com/apigw/commercial/spoton/bff/v1/getbestoffer',
        payload, { headers }
    );

    if (!bestOfferResponse.data || !bestOfferResponse.data.QuoteLineAndRoutingHeaders) {
        return { badResponse: true };
    }

    const quotes = bestOfferResponse.data.QuoteLineAndRoutingHeaders;
    const finalResults = [];

    for (const quote of quotes) {
        const nextDepartureIndex = quote.NextDepartureIndex;
        if (!nextDepartureIndex) continue;
        try {
            const detailsResponse = await axios.get(
                `https://www.cma-cgm.com/apigw/commercial/spoton/bff/v1/allocationandchargedetails/${nextDepartureIndex}`,
                { headers }
            );
            const cargoDetails = detailsResponse.data?.CargoChargeDetails || [];
            const prices = cargoDetails.map(charge => ({
                equipmentType: charge.EquipmentSizeType,
                oceanFreight: charge.OceanFreight?.Rate,
                totalCharge: charge.TotalCharge?.Rate,
                currency: charge.TotalCharge?.CurrencyCode || 'USD',
            }));
            finalResults.push({
                scheduleId: nextDepartureIndex,
                departureDate: quote.DepartureDate,
                arrivalDate: quote.ArrivalDate,
                transitTime: quote.TransitTime,
                vesselName: quote.VesselName,
                prices,
            });
        } catch (detailError) {
            console.error(`Failed to fetch details for index ${nextDepartureIndex}:`, detailError.message);
        }
    }
    return { finalResults };
};

const getCmaQuotes = async (req, res) => {
    try {
        const payload = req.body;
        let { tokenData, isFresh } = await getTokenWithMeta(SITE_NAME);

        if (!tokenData || !isFresh) {
            await scraperLock.refreshSite(SITE_NAME);
            ({ tokenData } = await getTokenWithMeta(SITE_NAME));
        }

        if (!tokenData || !tokenData.CMA_COOKIE || !tokenData.CMA_XSRF_TOKEN) {
            throw new Error('CMA-CGM tokens are missing even after refresh attempt.');
        }

        let result;
        try {
            result = await fetchQuotesWithToken(tokenData, payload);
        } catch (err) {
            if (err.response && (err.response.status === 401 || err.response.status === 403)) {
                await scraperLock.refreshSite(SITE_NAME);
                const refreshed = await getTokenWithMeta(SITE_NAME);
                if (!refreshed.tokenData) throw err;
                result = await fetchQuotesWithToken(refreshed.tokenData, payload);
            } else {
                throw err;
            }
        }

        if (result.badResponse) {
            return res.status(400).json({ success: false, message: 'No quotes found or invalid response' });
        }
        res.json({ success: true, data: result.finalResults });
    } catch (error) {
        console.error('Error fetching CMA quotes:', error.response ? error.response.data : error.message);
        res.status(500).json({
            success: false,
            message: 'Failed to fetch CMA quotes',
            error: error.response ? error.response.status : error.message,
        });
    }
};

module.exports = { getCmaQuotes };