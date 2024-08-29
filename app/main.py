from flask import Flask
from dotenv import load_dotenv
from app.routes.webhook import webhook

# Load environment variables
load_dotenv()

import logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)

# Register blueprints
app.register_blueprint(webhook)

if __name__ == '__main__':
    app.run(debug=True)