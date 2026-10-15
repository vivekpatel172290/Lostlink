import sys
import os

# Add parent directory to sys.path so app, config, models can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

app = create_app()

# Expose WSGI application for Vercel
if __name__ == "__main__":
    app.run()
