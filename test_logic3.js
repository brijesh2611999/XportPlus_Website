const masterRatesData = [];
const payload = { CommodityCode: 'FAK' };
const data = {
    "success": true,
    "data": [
        {
            "scheduleId": "4295dff3-755a-447c-b157-991fe286e09f",
            "departureDate": "2026-08-19T04:00:00+00:00",
            "arrivalDate": "2026-10-11T20:00:00+00:00",
            "transitTime": 54,
            "vesselName": "CSCL MERCURY",
            "prices": [
                {
                    "equipmentType": "20ST",
                    "oceanFreight": 5052.0,
                    "totalCharge": 5594.0,
                    "currency": "USD"
                }
            ]
        },
        {
            "scheduleId": "e1e98036-0b70-494f-a636-890bb5f42e22",
            "departureDate": "2026-09-01T14:00:00+00:00",
            "arrivalDate": "2026-10-11T20:00:00+00:00",
            "transitTime": 40,
            "vesselName": "CMA CGM ALEXANDER VON HUMBOLDT",
            "prices": []
        }
    ]
};

data.data.forEach((quote) => {
    const cmaCharges = [];
    let totalBuy = 0;
    
    if (quote.prices && quote.prices.length > 0) {
        const p = quote.prices[0];
        cmaCharges.push({ charge_name: "Ocean Freight", charge_type: "Base Freight", basis: "Per Container", rate: p.oceanFreight, amount: p.oceanFreight });
        if (p.totalCharge > p.oceanFreight) {
           const diff = p.totalCharge - p.oceanFreight;
           cmaCharges.push({ charge_name: "Surcharges & Origin THC", charge_type: "Surcharge", basis: "Flat", rate: diff, amount: diff });
        }
        totalBuy = p.totalCharge;
    }

    masterRatesData.push({
        id: "R-CMA-" + quote.scheduleId.split('-')[0].toUpperCase(),
        mode: "SEA_FCL",
        rate_source: "CMA-CGM Live API",
        carrier_name: "CMA CGM",
        carrier_code: "CMA",
        carrier_logo: "https://placehold.co/80x80/0284c7/ffffff?text=CMA",
        rate_type: "Ocean FCL Spot",
        origin: "CNSHA (Origin)",
        destination: "ESBCN (Dest)",
        transit_time: quote.transitTime + " Days",
        departure_date: quote.departureDate.split('T')[0],
        arrival_date: quote.arrivalDate.split('T')[0],
        vessel_voyage: quote.vesselName || "Unknown Vessel",
        equipment: "20' Standard",
        commodity: payload.CommodityCode,
        incoterm: "CIF",
        buy_price: totalBuy,
        currency: "USD",
        validity_until: quote.departureDate.split('T')[0],
        co2_emission: "N/A",
        charges: cmaCharges
    });
});

let currentMarginPercent = 15;
let cardHtml = '';
masterRatesData.forEach(rate => {
    const marginDecimal = currentMarginPercent / 100;
    const sellPrice = rate.buy_price * (1 + marginDecimal);
    const profitAmount = sellPrice - rate.buy_price;
    cardHtml += rate.origin.split(' ')[0] + ' ' + rate.buy_price.toFixed(2) + ' ' + profitAmount.toFixed(2) + ' ' + sellPrice.toFixed(2) + '\n';
});
console.log(cardHtml);
