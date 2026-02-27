from flask import Flask

app = Flask(__name__)
app.config["POSTS_DIR"] = "content"
app.config["OUTPUT_DIR"] = "docs"

from app import routes
