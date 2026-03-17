from flask import Flask
from config import SECRET_KEY

from routes.admin_routes import admin_bp
from routes.auth_routes import admin_auth_bp, voter_auth_bp
from routes.voter_routes import voter_bp
from routes.main_routes import main_bp

app = Flask(__name__)
app.secret_key = SECRET_KEY


# Register blueprints
app.register_blueprint(main_bp)
app.register_blueprint(admin_auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(voter_bp)
app.register_blueprint(voter_auth_bp)


if __name__ == "__main__":
    app.run(debug=True)