const masterRatesData = [
  {
    "id": "R-CMA-4295DFF3",
    "mode": "SEA_FCL",
    "rate_source": "CMA-CGM Live API",
    "carrier_name": "CMA CGM",
    "carrier_code": "CMA",
    "carrier_logo": "https://placehold.co/80x80/0284c7/ffffff?text=CMA",
    "rate_type": "Ocean FCL Spot",
    "origin": "CNSHA (Origin)",
    "destination": "ESBCN (Dest)",
    "transit_time": "54 Days",
    "departure_date": "2026-08-19",
    "arrival_date": "2026-10-11",
    "vessel_voyage": "CSCL MERCURY",
    "equipment": "20' Standard",
    "commodity": "FAK",
    "incoterm": "CIF",
    "buy_price": 5594,
    "currency": "USD",
    "validity_until": "2026-08-19",
    "co2_emission": "N/A",
    "charges": [
      {
        "charge_name": "Ocean Freight",
        "charge_type": "Base Freight",
        "basis": "Per Container",
        "rate": 5052,
        "amount": 5052
      }
    ]
  }
];

let activeFilterMode = 'ALL';
let carrierVal = 'ALL';
let equipVal = 'ALL';

const filteredRates = masterRatesData.filter(rate => {
    if (activeFilterMode !== 'ALL' && rate.mode !== activeFilterMode) return false;
    if (carrierVal !== 'ALL' && !rate.carrier_name.includes(carrierVal)) return false;
    
    if (equipVal !== 'ALL') {
        if (equipVal === '40HC' && !rate.equipment.includes('40HC')) return false;
        if (equipVal === '20GP' && !rate.equipment.includes('20GP')) return false;
        if (equipVal === 'LCL_CBM' && rate.mode !== 'SEA_LCL') return false;
        if (equipVal === 'AIR_KG' && rate.mode !== 'AIR') return false;
    }
    return true;
});

console.log('Filtered:', filteredRates.length);
