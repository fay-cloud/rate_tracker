from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
from .models import db, Provider, ExchangeRate, UserActivity # Import models
from .models import init_app as init_db_app # Import the db initializer

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

import os
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'ratefinder.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy with the app
init_db_app(app)


# --- Dummy Data Setup ---
# This function will initialize the database with some dummy data if it's empty.
def init_db_with_data():
    with app.app_context():
        db.create_all() # Create tables if they don't exist

        if Provider.query.count() == 0:
            print("Populating database with initial provider data...")
            providers_data = [
                {"name": "TapTap Send", "registration_link": "https://www.taptapsend.com/"},
                {"name": "Revolut", "registration_link": "https://www.revolut.com/"},
                {"name": "Remitly", "registration_link": "https://www.remitly.com/"},
                {"name": "Wise (TransferWise)", "registration_link": "https://wise.com/"}
            ]
            for p_data in providers_data:
                provider = Provider(name=p_data['name'], registration_link=p_data['registration_link'])
                db.session.add(provider)
            db.session.commit()
            print("Providers populated.")

        if ExchangeRate.query.count() == 0:
            print("Populating database with initial exchange rate data...")
            taptap = Provider.query.filter_by(name="TapTap Send").first()
            revolut = Provider.query.filter_by(name="Revolut").first()
            remitly = Provider.query.filter_by(name="Remitly").first()
            wise = Provider.query.filter_by(name="Wise (TransferWise)").first()

            # Ensure providers exist before trying to use their IDs
            if not all([taptap, revolut, remitly, wise]):
                print("Error: Not all providers found. Skipping rate population.")
                return

            rates_data = [
                {"provider_id": taptap.id, "currency_pair": "USD_EUR", "rate": 0.9210, "last_updated": datetime.utcnow()},
                {"provider_id": revolut.id, "currency_pair": "USD_EUR", "rate": 0.9255, "last_updated": datetime.utcnow()},
                {"provider_id": remitly.id, "currency_pair": "USD_EUR", "rate": 0.9180, "last_updated": datetime.utcnow()},
                {"provider_id": wise.id, "currency_pair": "USD_EUR", "rate": 0.9230, "last_updated": datetime.utcnow()},
                {"provider_id": taptap.id, "currency_pair": "USD_GBP", "rate": 0.7905, "last_updated": datetime.utcnow()},
                {"provider_id": revolut.id, "currency_pair": "USD_GBP", "rate": 0.7950, "last_updated": datetime.utcnow()},
                {"provider_id": remitly.id, "currency_pair": "USD_GBP", "rate": 0.7880, "last_updated": datetime.utcnow()},
                {"provider_id": wise.id, "currency_pair": "USD_GBP", "rate": 0.7920, "last_updated": datetime.utcnow()},
                {"provider_id": revolut.id, "currency_pair": "EUR_GBP", "rate": 0.8580, "last_updated": datetime.utcnow()},
                {"provider_id": wise.id, "currency_pair": "EUR_GBP", "rate": 0.8590, "last_updated": datetime.utcnow()},
            ]
            for r_data in rates_data:
                rate = ExchangeRate(**r_data)
                db.session.add(rate)
            db.session.commit()
            print("Exchange rates populated.")
        else:
            print("Database already contains data.")


@app.route('/')
def home():
    return "RateFinder Backend is running!"

@app.route('/api/currency-pairs', methods=['GET'])
def get_currency_pairs():
    try:
        pairs_query = db.session.query(ExchangeRate.currency_pair).distinct().all()
        pairs = [pair[0] for pair in pairs_query]
        if not pairs:
            return jsonify(["USD_EUR", "USD_GBP", "EUR_GBP"]) # Fallback
        return jsonify(pairs)
    except Exception as e:
        # Log the error e
        print(f"Error fetching currency pairs: {e}")
        return jsonify({"error": "Could not fetch currency pairs"}), 500


@app.route('/api/rates/<currency_pair>', methods=['GET'])
def get_rates(currency_pair):
    try:
        rates_data = ExchangeRate.query.join(Provider)\
                                       .filter(ExchangeRate.currency_pair == currency_pair.upper())\
                                       .order_by(ExchangeRate.rate)\
                                       .all()

        if not rates_data:
            return jsonify([]), 404

        result = []
        for er in rates_data:
            result.append({
                "provider": er.provider.name,
                "rate": er.rate,
                "register_link": er.provider.registration_link,
                "last_updated": er.last_updated.isoformat()
            })
        return jsonify(result)
    except Exception as e:
        print(f"Error fetching rates for {currency_pair}: {e}")
        return jsonify({"error": f"Could not fetch rates for {currency_pair}"}), 500

@app.route('/api/track-click', methods=['POST'])
def track_click():
    data = request.json
    provider_name = data.get('provider')
    currency_pair_viewed = data.get('currency_pair_viewed') # Optional from frontend

    if not provider_name:
        return jsonify({"status": "error", "message": "Provider name required"}), 400

    try:
        activity = UserActivity(
            action='register_click',
            provider_name=provider_name,
            currency_pair_viewed=currency_pair_viewed,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.add(activity)
        db.session.commit()
        return jsonify({"status": "success", "message": "Click tracked"}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error tracking click: {e}")
        return jsonify({"status": "error", "message": "Could not track click"}), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_db_with_data()
    app.run(debug=True, port=5000)
