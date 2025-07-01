# This file will contain utility functions for the backend.
# For example, functions to fetch data from external exchange rate APIs
# and to update the database.

import requests # Keep for potential future use, even if dummying now
from datetime import datetime
from .models import db, Provider, ExchangeRate # Import necessary models

# Placeholder for actual API URLs and keys - these would be in environment variables or a config file
PROVIDER_APIS_CONFIG = {
    "TapTap Send": {
        "api_url": "https://api.taptapsend.example.com/rates",
        "params_template": {"pair": "{source}{target}"}, # e.g., USDEUR
        "rate_path": ["data", "rate"], # How to access rate in JSON response
        "name_in_api": "TapTap Send" # If the API uses a specific name identifier
    },
    "Revolut": {
        "api_url": "https://api.revolut.example.com/exchange",
        "params_template": {"from": "{source}", "to": "{target}", "amount": "1"},
        "rate_path": ["rates", "{target}"], # Example: response.rates.EUR
        "name_in_api": "Revolut"
    },
    "Remitly": {
        "api_url": "https://api.remitly.example.com/v1/rates",
        "params_template": {"sourceCurrency": "{source}", "destinationCurrency": "{target}"},
        "rate_path": ["data", 0, "rate"], # Example: response.data[0].rate
        "name_in_api": "Remitly"
    },
    "Wise (TransferWise)": {
        "api_url": "https://api.wise.com/v1/rates", # This is a guess, Wise has a public API
        "params_template": {"source": "{source}", "target": "{target}"},
        "rate_path": ["rate"],
        "name_in_api": "Wise"
    }
}

# List of currency pairs your app will support
SUPPORTED_CURRENCY_PAIRS = ["USD_EUR", "USD_GBP", "EUR_GBP", "CAD_USD"]


def fetch_rate_from_external_api(provider_name, currency_pair_str):
    """
    Simulates fetching an exchange rate for a given currency pair from a specific provider's API.
    In a real application, this function would make an HTTP request to the provider's API
    and parse the response. For now, it returns a dummy rate or None.
    """
    print(f"Attempting to fetch rate for {provider_name} - {currency_pair_str} from external API (simulation)...")

    # Simulate some variability and potential failures
    # This is highly simplified. Real API integration is complex.
    source_curr, target_curr = currency_pair_str.split('_')

    # Dummy rates (can be adjusted for more realistic simulation)
    # These are just examples and don't reflect real market data.
    base_rates = {
        "USD_EUR": 0.92,
        "USD_GBP": 0.79,
        "EUR_GBP": 0.85,
        "CAD_USD": 0.73
    }

    if currency_pair_str not in base_rates:
        print(f"  Unsupported currency pair for simulation: {currency_pair_str}")
        return None

    # Simulate slight variations per provider
    rate_adjustment = {
        "TapTap Send": 0.001,
        "Revolut": 0.0005,
        "Remitly": -0.001,
        "Wise (TransferWise)": 0.000
    }

    simulated_rate = base_rates[currency_pair_str] + rate_adjustment.get(provider_name, 0)

    # Simulate a small chance of API failure for a provider/pair
    import random
    if random.random() < 0.1: # 10% chance of "API failure"
        print(f"  SIMULATED API FAILURE for {provider_name} - {currency_pair_str}")
        return None

    print(f"  Successfully fetched (simulated) rate for {provider_name} - {currency_pair_str}: {simulated_rate}")
    return simulated_rate


def update_rates_for_provider(provider_obj, currency_pair_str):
    """
    Fetches and updates/creates the exchange rate for a specific provider and currency pair.
    """
    rate_value = fetch_rate_from_external_api(provider_obj.name, currency_pair_str)

    if rate_value is not None:
        # Check if a rate already exists for this provider and pair
        exchange_rate_entry = ExchangeRate.query.filter_by(
            provider_id=provider_obj.id,
            currency_pair=currency_pair_str
        ).first()

        if exchange_rate_entry:
            # Update existing rate
            exchange_rate_entry.rate = rate_value
            exchange_rate_entry.last_updated = datetime.utcnow()
            print(f"  Updating rate for {provider_obj.name} - {currency_pair_str} to {rate_value}")
        else:
            # Create new rate entry
            exchange_rate_entry = ExchangeRate(
                provider_id=provider_obj.id,
                currency_pair=currency_pair_str,
                rate=rate_value,
                last_updated=datetime.utcnow()
            )
            db.session.add(exchange_rate_entry)
            print(f"  Creating new rate for {provider_obj.name} - {currency_pair_str}: {rate_value}")

        # db.session.commit() will be called once at the end of update_all_rates
        return True
    return False


def update_all_rates_from_apis():
    """
    Scheduled job to fetch rates from all external APIs for all configured providers
    and supported currency pairs, then updates the database.
    This function needs to be called within a Flask app context if it interacts with the DB.
    """
    print(f"[{datetime.utcnow()}] Starting scheduled rate update job...")

    providers = Provider.query.all()
    if not providers:
        print("No providers found in the database. Cannot update rates.")
        return

    successful_updates = 0
    failed_updates = 0

    for provider in providers:
        # Check if this provider is in our API config (optional, good for flexibility)
        if provider.name not in PROVIDER_APIS_CONFIG:
            print(f"  Skipping {provider.name}: No API configuration found.")
            continue

        print(f"Fetching rates for provider: {provider.name}")
        for pair_str in SUPPORTED_CURRENCY_PAIRS:
            try:
                if update_rates_for_provider(provider, pair_str):
                    successful_updates += 1
                else:
                    failed_updates +=1
            except Exception as e:
                print(f"  ERROR processing {provider.name} - {pair_str}: {e}")
                failed_updates += 1
                db.session.rollback() # Rollback for this specific error, or handle more globally

    try:
        db.session.commit()
        print("Successfully committed rate updates to the database.")
    except Exception as e:
        db.session.rollback()
        print(f"Error committing rate updates to database: {e}")
        # Potentially re-raise or log more severely

    print(f"[{datetime.utcnow()}] Scheduled rate update job finished.")
    print(f"Summary: Successful updates: {successful_updates}, Failed attempts: {failed_updates}")


# Example of how you might call this from a script or a Flask CLI command
# Make sure this is run within an application context if you're testing it standalone.
if __name__ == '__main__':
    # This standalone execution requires a Flask app context to work with the database.
    # You would typically set up a Flask app instance here for testing.
    # For example:
    # from app import app as flask_app
    # with flask_app.app_context():
    #     # Ensure DB is initialized if you're running this for the first time
    #     # from models import db
    #     # db.create_all()
    #     # You might also need to populate Providers if they don't exist
    #     update_all_rates_from_apis()
    print("To test utils.py standalone, you need to run it within a Flask application context.")
    print("Consider creating a Flask CLI command or a test script that sets up the app context.")
