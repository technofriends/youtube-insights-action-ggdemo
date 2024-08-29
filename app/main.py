from flask import Flask
from dotenv import load_dotenv
from app.routes.webhook import webhook

load_dotenv()

import logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.register_blueprint(webhook)

if __name__ == '__main__':
    app.run(debug=True)