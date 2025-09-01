#app.py

import logging
import os
import sys
from flask import Flask
from config import cfg
from sbcutils import PyRibbonClient
from routes import bp

# Setup logging before anything else
logfile = os.path.join(os.path.dirname(__file__), "audssoncall.log")
if not os.path.exists(logfile):
    open(logfile, 'a').close()

# Configure root logger (shared globally)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(logfile, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)  # Optional, also log to stdout
    ]
)

# Initialize logger for this module
logging.info("Starting Auds on Call application...")

# --- FLASK APP INITIALIZATION ---
app = Flask(__name__ , static_url_path="/audssoncall/static")
app.config.from_object(cfg)
sbc_client = PyRibbonClient()
# This is the ONLY route-related action in app.py
app.register_blueprint(bp, url_prefix='/audssoncall')

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
