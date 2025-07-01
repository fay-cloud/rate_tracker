document.addEventListener('DOMContentLoaded', () => {
    const currencyPairSelect = document.getElementById('currencyPairSelect');
    const providerListContainer = document.getElementById('providerListContainer');

    // --- For Currency Converter ---
    const amountInput = document.getElementById('amountInput');
    const fromCurrencySelect = document.getElementById('fromCurrencySelect');
    const toCurrencySelect = document.getElementById('toCurrencySelect');
    const convertButton = document.getElementById('convertButton');
    const convertedAmountSpan = document.getElementById('convertedAmount');

    // --- Configuration ---
    // In a real app, this might come from a config file or another API endpoint
    const API_BASE_URL = 'http://localhost:5000/api'; // Assuming backend runs on port 5000

    let allRatesData = {}; // To store rates for the converter: { "USD_EUR": { "TapTap": 0.92, ... }, ... }
    let availableCurrencies = new Set(); // To populate converter dropdowns: {"USD", "EUR", "GBP"}

    // Function to fetch available currency pairs
    async function fetchCurrencyPairs() {
        try {
            const response = await fetch(`${API_BASE_URL}/currency-pairs`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const pairs = await response.json();
            populateCurrencyPairDropdown(pairs);
            populateConverterCurrencyDropdowns(extractCurrenciesFromPairs(pairs));
        } catch (error) {
            console.error("Failed to fetch currency pairs:", error);
            currencyPairSelect.innerHTML = '<option value="">Error loading pairs</option>';
        }
    }

    // Function to extract unique currencies from pairs
    function extractCurrenciesFromPairs(pairs) {
        pairs.forEach(pair => {
            const currencies = pair.split('_');
            availableCurrencies.add(currencies[0]);
            availableCurrencies.add(currencies[1]);
        });
        return Array.from(availableCurrencies);
    }

    // Function to populate the main currency pair dropdown
    function populateCurrencyPairDropdown(pairs) {
        currencyPairSelect.innerHTML = '<option value="">Select a pair</option>'; // Clear loading/error
        pairs.forEach(pair => {
            const option = document.createElement('option');
            option.value = pair;
            option.textContent = pair.replace('_', '/');
            currencyPairSelect.appendChild(option);
        });
    }

    // Function to populate currency dropdowns for the converter
    function populateConverterCurrencyDropdowns(currencies) {
        fromCurrencySelect.innerHTML = '';
        toCurrencySelect.innerHTML = '';
        currencies.forEach(currency => {
            const optionFrom = document.createElement('option');
            optionFrom.value = currency;
            optionFrom.textContent = currency;
            fromCurrencySelect.appendChild(optionFrom);

            const optionTo = document.createElement('option');
            optionTo.value = currency;
            optionTo.textContent = currency;
            toCurrencySelect.appendChild(optionTo);
        });
        // Set default different values if possible
        if (currencies.length > 1) {
            fromCurrencySelect.value = currencies[0];
            toCurrencySelect.value = currencies[1];
        }
    }

    // Function to fetch rates for a selected currency pair
    async function fetchRatesForPair(pair) {
        if (!pair) {
            providerListContainer.innerHTML = '<p class="loading-message">Select a currency pair to see rates.</p>';
            allRatesData[pair] = {}; // Clear rates for this pair
            return;
        }
        providerListContainer.innerHTML = '<p class="loading-message">Loading rates...</p>';
        try {
            const response = await fetch(`${API_BASE_URL}/rates/${pair}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const rates = await response.json();
            displayRates(rates, pair);
            storeRatesForConverter(pair, rates);
        } catch (error) {
            console.error(`Failed to fetch rates for ${pair}:`, error);
            providerListContainer.innerHTML = `<p class="error-message">Error loading rates for ${pair}. Please try again.</p>`;
            allRatesData[pair] = {}; // Clear rates on error
        }
    }

    // Function to display rates in the provider list
    function displayRates(rates, pair) {
        providerListContainer.innerHTML = ''; // Clear previous content
        if (rates.length === 0) {
            providerListContainer.innerHTML = `<p class="loading-message">No rates found for ${pair.replace('_', '/')}.</p>`;
            return;
        }

        rates.forEach(rateInfo => {
            const card = document.createElement('div');
            card.className = 'provider-card';
            card.innerHTML = `
                <div class="provider-info">
                    <h3>${rateInfo.provider}</h3>
                    <p class="rate">${rateInfo.rate.toFixed(4)} ${pair.split('_')[1]}</p>
                    <p class="pair-info">(1 ${pair.split('_')[0]} = ${rateInfo.rate.toFixed(4)} ${pair.split('_')[1]})</p>
                </div>
                <a href="${rateInfo.register_link}" class="register-button" target="_blank" rel="noopener noreferrer" data-provider="${rateInfo.provider}">Register</a>
            `;
            // Add event listener for tracking clicks (optional)
            // card.querySelector('.register-button').addEventListener('click', handleRegisterClick);
            providerListContainer.appendChild(card);
        });
    }

    // Store rates in a structured way for the converter
    function storeRatesForConverter(pair, ratesList) {
        if (!allRatesData[pair]) {
            allRatesData[pair] = {};
        }
        ratesList.forEach(rateInfo => {
            allRatesData[pair][rateInfo.provider] = rateInfo.rate;
        });
        // For direct conversion (e.g. EUR to USD), we need inverse rates or separate API calls
        // For simplicity, this converter will primarily use USD as a base or use the first provider's rate.
    }

    // --- Currency Converter Logic ---
    function convertCurrency() {
        const amount = parseFloat(amountInput.value);
        const fromCurrency = fromCurrencySelect.value;
        const toCurrency = toCurrencySelect.value;

        if (isNaN(amount) || !fromCurrency || !toCurrency) {
            convertedAmountSpan.textContent = "Invalid input";
            return;
        }

        if (fromCurrency === toCurrency) {
            convertedAmountSpan.textContent = `${amount.toFixed(2)} ${toCurrency}`;
            return;
        }

        // Try to find a direct rate (e.g. USD_EUR)
        let rate = findRate(fromCurrency, toCurrency);

        if (rate) {
            convertedAmountSpan.textContent = `${(amount * rate).toFixed(2)} ${toCurrency}`;
        } else {
            // Try to find an inverse rate (e.g. EUR_USD from USD_EUR)
            rate = findRate(toCurrency, fromCurrency);
            if (rate) {
                convertedAmountSpan.textContent = `${(amount / rate).toFixed(2)} ${toCurrency}`;
            } else {
                // Try cross-conversion via USD (or another common currency)
                // This requires rates like FROM_USD and TO_USD (or USD_FROM and USD_TO)
                const fromToUsdRate = findRate(fromCurrency, "USD");
                const usdToToRate = findRate("USD", toCurrency);

                if (fromToUsdRate && usdToToRate) {
                    convertedAmountSpan.textContent = `${(amount * fromToUsdRate * usdToToRate).toFixed(2)} ${toCurrency}`;
                } else {
                     convertedAmountSpan.textContent = "Rate not available";
                }
            }
        }
    }

    // Helper to find a rate from stored data (averages or picks first available)
    function findRate(sourceCurr, targetCurr) {
        const pairKey = `${sourceCurr}_${targetCurr}`;
        if (allRatesData[pairKey]) {
            // Use the rate from the first provider for simplicity, or average them
            const providers = Object.keys(allRatesData[pairKey]);
            if (providers.length > 0) {
                return allRatesData[pairKey][providers[0]];
            }
        }
        return null;
    }

    // --- Event Listeners ---
    currencyPairSelect.addEventListener('change', (event) => {
        fetchRatesForPair(event.target.value);
    });

    convertButton.addEventListener('click', convertCurrency);

    // Optional: Track register clicks
    // function handleRegisterClick(event) {
    //     const provider = event.target.dataset.provider;
    //     // Send data to backend to log this click
    //     fetch(`${API_BASE_URL}/track-click`, {
    //         method: 'POST',
    //         headers: { 'Content-Type': 'application/json' },
    //         body: JSON.stringify({ provider: provider, source: 'RateFinderApp' })
    //     })
    //     .then(response => response.json())
    //     .then(data => console.log('Track click response:', data))
    //     .catch(error => console.error('Error tracking click:', error));
    //     // The link will open in a new tab due to target="_blank"
    // }


    // --- Initial Load ---
    fetchCurrencyPairs(); // Load currency pairs for the main dropdown
    // Converter dropdowns will be populated after pairs are fetched

    // Placeholder for logo - replace 'logo_placeholder.png' with your actual logo file in 'images/'
    const appLogo = document.getElementById('appLogo');
    if (!appLogo.src.includes('logo_placeholder.png')) { // Basic check if you've replaced it
        // You might want to dynamically set it if its path is configurable
    } else {
        // Could add a more visible placeholder if the image is missing
        // appLogo.alt = "RateFinder (Logo Missing)";
    }

    // TODO: Implement auto-refresh logic if strictly "real-time daily" means more than on page load/pair selection.
    // For daily rates, fetching on selection or page load is often sufficient.
    // If backend updates rates at a specific time, frontend could poll or use websockets.
    // A simpler "daily" refresh could be a meta refresh tag or a JS timeout that re-fetches.
    // setInterval( () => {
    //    const selectedPair = currencyPairSelect.value;
    //    if(selectedPair) fetchRatesForPair(selectedPair);
    // }, 24 * 60 * 60 * 1000); // Refresh every 24 hours - crude, better to align with backend update
});
