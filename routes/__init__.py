from flask import Flask
from data.database import PotatoDatabase

db = PotatoDatabase("data")
api = Flask(__name__)

from . import bloq
from . import locker
from . import rent
