import sys
path = '/home/LuisRaja/deckstation.id'
if path not in sys.path:
    sys.path.append(path)
from app import app as application
