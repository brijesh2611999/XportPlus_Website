const axios = require('axios');
const { getTokenWithMeta } = require('../config/db');
const scraperLock = require('../services/scraperLock');
require('dotenv').config();

const SITE_NAME = 'MSC';

// NOTE: same placeholder GraphQL query/variables as before — origin/destination
// IDs are hardcoded to one lane. Worth building a real location-lookup before
// this goes further, but leaving that as-is here since it's a separate task
// from the auth/refresh fix.
const buildGraphqlPayload = (payload) => {
    // Kept identical to the field set you had working — do not trim this,
    // MSC's schema needs the full nested selection or fields silently come back null.
    const graphqlPayloadString = `{"query":"\\n    query InstantQuoteSearchV5($input: RateCardSearchCriteriaInput!) {\\n  searchRateCardsV5(request: $input) {\\n    myMscId\\n    shippingWindowBasedGroups {\\n      validFrom\\n      validTo\\n      quoteExpiration\\n      totalMinTransitDays\\n      totalMaxTransitDays\\n      oceanTranshipmentModes\\n      sizeTypeAndBestPrices {\\n        sizeType\\n        price\\n        currency\\n      }\\n      rateCards {\\n        myMscId\\n        rateValidity\\n        quoteExpiration\\n        sizeType\\n        oceanRateValidFrom\\n        oceanRateValidTo\\n        inlandTransitDays\\n        quantity\\n        isSelected\\n        total\\n        unitTotal\\n        subTotal\\n        displayTotal\\n        displaySubTotal\\n        displayUnitTotal\\n        displayTotalAmountPerBillOfLading\\n        displayTotalAmountPerEquipment\\n        shipmentTerm\\n        currency\\n        tariffId\\n        commodityGroup\\n        weight\\n        weightUnit\\n        reference\\n        quoteIssued\\n        comments\\n        temperatureUnit\\n        externalReference\\n        rateCardType\\n        paymentMethods\\n        publicationChannel\\n        totalAmountPerBillOfLading\\n        totalAmountPerEquipment\\n        convertedTemperatureUnit\\n        minTemperature\\n        maxTemperature\\n        temperatureUnit\\n        convertedMinTemperature\\n        convertedMaxTemperature\\n        convertedMinWeight\\n        convertedMaxWeight\\n        convertedWeightUnit\\n        hasChargesPaymentMethods\\n        commodityHarmonizedSystemCodesExclusions {\\n          harmonizedSystemCodeId\\n          nomenclatureCode\\n        }\\n        containerSpecifications {\\n          containerSizeTypeId\\n          isNonOperatingReefer\\n          sizeAndType\\n        }\\n        origin {\\n          inland {\\n            id\\n            name\\n            longDisplayName\\n            transportationMode\\n            transitTimeDays\\n            transportationMode\\n            zipcode\\n            depotLocationName\\n            depotLocationUnCode\\n            countryCode\\n            unCode\\n            stateCode\\n          }\\n          port {\\n            id\\n            name\\n            unCode\\n            longDisplayName\\n            countryCode\\n          }\\n        }\\n        destination {\\n          inland {\\n            id\\n            name\\n            longDisplayName\\n            transportationMode\\n            transitTimeDays\\n            zipcode\\n            depotLocationName\\n            depotLocationUnCode\\n            countryCode\\n            unCode\\n            stateCode\\n          }\\n          port {\\n            id\\n            name\\n            unCode\\n            longDisplayName\\n            countryCode\\n          }\\n        }\\n        chargesGroup {\\n          chargeType\\n          charges {\\n            myMscId\\n            chargeDescription\\n            allowedPaymentMethods\\n            selectedPaymentMethod\\n            isFollowingFreightPaymentMethod\\n            isIncludedInFreight\\n            addToFreightRate\\n            isLia\\n            chargeLevel\\n            amountConvertedToFreightChargeCurrency\\n            commentsAndConditions\\n            validFrom\\n            validTo\\n            chargeType\\n            longDisplayName\\n            reference\\n            currency\\n            amount\\n            freightAmount\\n            applicability\\n            applicabilityToFreightAmount\\n            chargeCodeId\\n            code\\n            dtx\\n            calculationMethod\\n            calculationMethodAmount\\n            calculationType\\n            calculationWeightUnit\\n            isToBeCalculated\\n            bookingSourceType\\n            shippingInstructionsSourceType\\n            isLocal\\n            isPaidWithFreight\\n            isCancellationFee\\n            isNoShowFee\\n            isElectronicBillOfLading\\n            isConditionalTariffCharge\\n            isCommodityConditionalChargeBased\\n            isWaived\\n          }\\n          defaultPaymentMethod\\n          selectedPaymentMethod\\n        }\\n        scheduleInformation {\\n          vesselTransitTimeInMinutes\\n          oceanTransitDays\\n          vesselTransitTime\\n          vesselRouteList\\n          oceanTranshipmentMode\\n          totalTransitDays\\n          departureDate\\n          arrivalDate\\n          serviceName\\n          legsDetails {\\n            legSequence\\n            maritimeServiceName\\n            arrivalPortName\\n          }\\n        }\\n        freeTimeInformation {\\n          import {\\n            type\\n            text\\n          }\\n          export {\\n            type\\n            text\\n          }\\n        }\\n      }\\n    }\\n    vesselBasedGroups {\\n      oceanTranshipmentMode\\n      vessel {\\n        imoNumber\\n        name\\n        vesselId\\n        voyageCode\\n      }\\n      sizeTypeAndBestPrices {\\n        sizeType\\n        price\\n        currency\\n      }\\n      rateCards {\\n        myMscId\\n        rateValidity\\n        quoteExpiration\\n        sizeType\\n        oceanRateValidFrom\\n        oceanRateValidTo\\n        inlandTransitDays\\n        quantity\\n        isSelected\\n        total\\n        unitTotal\\n        subTotal\\n        displayTotal\\n        displaySubTotal\\n        displayUnitTotal\\n        displayTotalAmountPerBillOfLading\\n        displayTotalAmountPerEquipment\\n        shipmentTerm\\n        currency\\n        tariffId\\n        commodityGroup\\n        weight\\n        weightUnit\\n        reference\\n        quoteIssued\\n        comments\\n        temperatureUnit\\n        externalReference\\n        rateCardType\\n        paymentMethods\\n        publicationChannel\\n        totalAmountPerBillOfLading\\n        totalAmountPerEquipment\\n        convertedTemperatureUnit\\n        minTemperature\\n        maxTemperature\\n        temperatureUnit\\n        convertedMinTemperature\\n        convertedMaxTemperature\\n        convertedMinWeight\\n        convertedMaxWeight\\n        convertedWeightUnit\\n        hasChargesPaymentMethods\\n        commodityHarmonizedSystemCodesExclusions {\\n          harmonizedSystemCodeId\\n          nomenclatureCode\\n        }\\n        containerSpecifications {\\n          containerSizeTypeId\\n          isNonOperatingReefer\\n          sizeAndType\\n        }\\n        origin {\\n          inland {\\n            id\\n            name\\n            longDisplayName\\n            transportationMode\\n            transitTimeDays\\n            transportationMode\\n            zipcode\\n            depotLocationName\\n            depotLocationUnCode\\n            countryCode\\n            unCode\\n            stateCode\\n          }\\n          port {\\n            id\\n            name\\n            unCode\\n            longDisplayName\\n            countryCode\\n          }\\n        }\\n        destination {\\n          inland {\\n            id\\n            name\\n            longDisplayName\\n            transportationMode\\n            transitTimeDays\\n            zipcode\\n            depotLocationName\\n            depotLocationUnCode\\n            countryCode\\n            unCode\\n            stateCode\\n          }\\n          port {\\n            id\\n            name\\n            unCode\\n            longDisplayName\\n            countryCode\\n          }\\n        }\\n        chargesGroup {\\n          chargeType\\n          charges {\\n            myMscId\\n            chargeDescription\\n            allowedPaymentMethods\\n            selectedPaymentMethod\\n            isFollowingFreightPaymentMethod\\n            isIncludedInFreight\\n            addToFreightRate\\n            isLia\\n            chargeLevel\\n            amountConvertedToFreightChargeCurrency\\n            commentsAndConditions\\n            validFrom\\n            validTo\\n            chargeType\\n            longDisplayName\\n            reference\\n            currency\\n            amount\\n            freightAmount\\n            applicability\\n            applicabilityToFreightAmount\\n            chargeCodeId\\n            code\\n            dtx\\n            calculationMethod\\n            calculationMethodAmount\\n            calculationType\\n            calculationWeightUnit\\n            isToBeCalculated\\n            bookingSourceType\\n            shippingInstructionsSourceType\\n            isLocal\\n            isPaidWithFreight\\n            isCancellationFee\\n            isNoShowFee\\n            isElectronicBillOfLading\\n            isConditionalTariffCharge\\n            isCommodityConditionalChargeBased\\n            isWaived\\n          }\\n          defaultPaymentMethod\\n          selectedPaymentMethod\\n        }\\n        scheduleInformation {\\n          vesselTransitTimeInMinutes\\n          oceanTransitDays\\n          vesselTransitTime\\n          vesselRouteList\\n          oceanTranshipmentMode\\n          totalTransitDays\\n          departureDate\\n          arrivalDate\\n          serviceName\\n          legsDetails {\\n            legSequence\\n            maritimeServiceName\\n            arrivalPortName\\n          }\\n        }\\n        freeTimeInformation {\\n          import {\\n            type\\n            text\\n          }\\n          export {\\n            type\\n            text\\n          }\\n        }\\n        vessel {\\n          imoNumber\\n          name\\n          vesselId\\n          voyageCode\\n        }\\n      }\\n    }\\n    rateCardSearchCriteria {\\n      weightUnit\\n      portOrLocationAtOrigin {\\n        id\\n        portId\\n        name\\n        longDisplayName\\n        unCode\\n        zipcode\\n        isInlandLocation\\n        transportationMode\\n        countryCode\\n        cargoCountry {\\n          countryId\\n          longDisplayName\\n          name\\n          isoAlpha2Code\\n        }\\n      }\\n      cargoValue\\n      portOrLocationAtDestination {\\n        id\\n        portId\\n        name\\n        longDisplayName\\n        unCode\\n        zipcode\\n        isInlandLocation\\n        transportationMode\\n        countryCode\\n        cargoCountry {\\n          countryId\\n          longDisplayName\\n          name\\n          isoAlpha2Code\\n        }\\n      }\\n      equipmentFilter {\\n        equipmentType\\n        weightValue\\n      }\\n      validTo\\n      validFrom\\n      commodityGroupCode\\n      commodityGroupDescription\\n      temperature\\n      temperatureUnit\\n    }\\n    searchErrorInfo {\\n      errorId\\n      errorDescription\\n    }\\n  }\\n  defaultMscCompanyForUser {\\n    name\\n    companyAddress\\n    mscCode\\n    isDefaultCompany\\n    agency\\n    agencyId\\n    agencyIdCompanyCode\\n  }\\n}\\n    \",\"variables\":{\"input\":{\"originId\":234316,\"isOriginAPort\":true,\"destinationId\":8714,\"isDestinationAPort\":false,\"originTransportationMode\":\"\",\"destinationTransportationMode\":\"Door\",\"originZipcode\":\"\",\"destinationZipcode\":\"\",\"equipmentFilter\":[{\"equipmentType\":\"20DV\",\"weightValue\":18000},{\"equipmentType\":\"40DV\",\"weightValue\":18000},{\"equipmentType\":\"40HC\",\"weightValue\":18000}],\"weightUnit\":\"Kgs\",\"commodityGroupCode\":\"\",\"temperature\":null,\"temperatureUnit\":null,\"cargoValue\":null,\"cargoDestinationCountryId\":230,\"cargoOriginCountryId\":103,\"commodityGroupDescription\":\"\"}},\"operationName\":\"InstantQuoteSearchV5\"}`;
    return JSON.parse(graphqlPayloadString);
};

const buildHeaders = (tokenData) => ({
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'authorization': `Bearer ${tokenData.MSC_BEARER_TOKEN}`,
    'content-type': 'application/json',
    'origin': 'https://www.mymsc.com',
    'referer': 'https://www.mymsc.com/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
});

const fetchQuotesWithToken = async (tokenData, payload) => {
    const headers = buildHeaders(tokenData);
    const graphqlPayload = buildGraphqlPayload(payload);

    const response = await axios.post(
        'https://services.mymsc.com/quote/graphql',
        graphqlPayload,
        { headers }
    );
    const mscData = response.data;

    if (!mscData.data || !mscData.data.searchRateCardsV5) {
        return { badResponse: true };
    }

    const groups = mscData.data.searchRateCardsV5.shippingWindowBasedGroups || [];
    const finalResults = [];

    groups.forEach(group => {
        let requestedSize = '20DV';
        if (payload.Equipments && payload.Equipments[0].EquipmentSizeType === '40ST') {
            requestedSize = '40DV';
        }

        const bestPrice = group.sizeTypeAndBestPrices.find(p => p.sizeType === requestedSize);

        if (bestPrice) {
            finalResults.push({
                scheduleId: Math.random().toString(36).substring(7),
                departureDate: group.validFrom || new Date().toISOString(),
                arrivalDate: group.quoteExpiration || new Date().toISOString(),
                transitTime: group.totalMinTransitDays,
                vesselName: 'MSC VESSEL (TBD)',
                shippingLine: 'MSC',
                prices: [{
                    equipmentType: payload.Equipments ? payload.Equipments[0].EquipmentSizeType : '20ST',
                    oceanFreight: bestPrice.price - 500,
                    totalCharge: bestPrice.price,
                    currency: bestPrice.currency,
                }],
            });
        }
    });

    return { finalResults };
};

const getMscQuotes = async (req, res) => {
    try {
        const payload = req.body;

        let { tokenData, isFresh } = await getTokenWithMeta(SITE_NAME);

        if (!tokenData || !isFresh) {
            console.log(`MSC token missing/stale (fresh=${isFresh}) — refreshing before request.`);
            await scraperLock.refreshSite(SITE_NAME);
            ({ tokenData } = await getTokenWithMeta(SITE_NAME));
        }

        if (!tokenData || !tokenData.MSC_BEARER_TOKEN) {
            throw new Error('MSC tokens are missing even after refresh attempt.');
        }

        let result;
        try {
            result = await fetchQuotesWithToken(tokenData, payload);
        } catch (err) {
            if (err.response && (err.response.status === 401 || err.response.status === 403)) {
                console.log('MSC rejected token (401/403) — forcing refresh and retrying once.');
                await scraperLock.refreshSite(SITE_NAME);
                const refreshed = await getTokenWithMeta(SITE_NAME);
                if (!refreshed.tokenData) throw err;
                result = await fetchQuotesWithToken(refreshed.tokenData, payload);
            } else {
                throw err;
            }
        }

        if (result.badResponse) {
            return res.status(400).json({ success: false, message: 'Invalid response from MSC' });
        }

        res.json({ success: true, data: result.finalResults });
    } catch (error) {
        console.error('Error fetching MSC quotes:', error.response ? error.response.data : error.message);
        res.status(500).json({
            success: false,
            message: 'Failed to fetch MSC quotes',
            error: error.response ? error.response.status : error.message,
        });
    }
};

module.exports = {
    getMscQuotes,
};