from flask import Flask, render_template, request
import sqlite3
import requests
import time
import threading

app = Flask(__name__)

# It's better to define the database path and connect/create cursors when needed
DATABASE = 'currency_exchange.db'

def get_db_conn():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row # Optional: allows accessing columns by name
    return conn

# Create required tables
def init_db():
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS platforms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            rate REAL
        );
    ''')
    conn.commit()
    conn.close()

init_db() # Initialize the database and table when the app starts

# Define a function to fetch exchange rates from multiple platforms
def fetch_exchange_rates():
    # Using dummy data as actual web scraping is complex and API-dependent
    # For a real app, you'd query each platform's API
    # Example: response = requests.get(f'https://api.{platform}.com/exchange-rate')
    #          exchange_rates[platform] = response.json()['rate']
    dummy_rates = {
        'Remitly': 1.12,  # Example rate
        'TransferWise': 1.15, # Example rate
        'Platform3': 1.10 # Example rate
        # Add up to 10 platforms here
    }
    return dummy_rates

# Define a function to update exchange rates in real-time
def update_exchange_rates_periodically():
    while True:
        print("Fetching and updating exchange rates...")
        exchange_rates = fetch_exchange_rates()
        try:
            conn = get_db_conn()
            c = conn.cursor()
            for platform, rate in exchange_rates.items():
                # Using INSERT OR IGNORE for new platforms, and UPDATE for existing ones
                c.execute('INSERT OR IGNORE INTO platforms (name, rate) VALUES (?, ?)', (platform, rate))
                c.execute('UPDATE platforms SET rate = ? WHERE name = ?', (rate, platform))
            conn.commit()
            print(f"Rates updated: {exchange_rates}")
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            if conn:
                conn.close()
        time.sleep(300)  # Update every 5 minutes (300 seconds)

# Define a route to display exchange rates from multiple platforms
@app.route('/')
def index():
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('SELECT name, rate FROM platforms')
    # Fetchall returns a list of tuples, convert to dict for easier template access
    db_rates = c.fetchall()
    conn.close()

    # Convert list of Row objects to a dictionary
    exchange_rates_display = {row['name']: row['rate'] for row in db_rates}

    # If database is empty, fetch fresh rates immediately for display
    if not exchange_rates_display:
        exchange_rates_display = fetch_exchange_rates()

    return render_template('index.html', exchange_rates=exchange_rates_display)

# Define a route to handle the "Get" button click event
@app.route('/register/<platform>')
def register(platform):
    # Redirect the user to the platform's registration page
    # These are placeholder URLs
    platform_urls = {
        'Remitly': 'https://www.remitly.com',
        'TransferWise': 'https://www.wise.com', # TransferWise is now Wise
        'Platform3': 'https://www.example.com/platform3'
    }
    url = platform_urls.get(platform, 'https://www.example.com/register') # Default fallback
    # For a real app, you would redirect: return redirect(url)
    # For now, just showing the URL
    return f'Would redirect to: {url}'


if __name__ == '__main__':
    # Start the rate update thread
    update_thread = threading.Thread(target=update_exchange_rates_periodically)
    update_thread.daemon = True  # Allows main program to exit even if thread is running
    update_thread.start()

    # Run the Flask development server
    app.run(debug=True, use_reloader=False) # use_reloader=False is important when using threads like this for background tasks
                                            # to prevent the background task from running twice.
                                            # For production, use a proper WSGI server.
