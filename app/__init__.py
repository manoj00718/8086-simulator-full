from flask import Flask

def create_app():
    app = Flask(__name__)
    
    from app.routes.main_routes import main_bp
    app.secret_key = "a53581eb8ee47dab2977cbbb6f997a69e4b66c6ea0e61e619e28f9b19f068308"
    app.register_blueprint(main_bp)

    return app
