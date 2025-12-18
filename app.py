from flask import Flask
from datetime import timedelta

def create_app():
    app = Flask(__name__)

    # 🔐 Secret key (move to env var in production)
    app.secret_key = "super-secret-key"

    # 🔒 Session security
    app.permanent_session_lifetime = timedelta(hours=8)

    # 📌 Register Blueprints
    from routes.auth_routes import auth_bp
    from routes.dashboard_routes import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)

    return app


# 🚀 Entry point
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
