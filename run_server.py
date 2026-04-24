#!/usr/bin/env python3
import sys
import os

# Add the project directory to path
sys.path.insert(0, '/home/indra/.local/share/opencode/worktree/7dde875492ee88cb7096a08a608792e33bff079a/sunny-star')
os.chdir('/home/indra/.local/share/opencode/worktree/7dde875492ee88cb7096a08a608792e33bff079a/sunny-star')

# Set environment
os.environ['FLASK_APP'] = 'app.py'

# Run the Flask app
from app import app
app.run(debug=False, port=5001, host='0.0.0.0')