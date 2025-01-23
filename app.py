"""
This is the API entry point. It does nothing special besides calling the run
method on the Flask api.
"""

from routes import api

if __name__ == '__main__':
    api.run()
