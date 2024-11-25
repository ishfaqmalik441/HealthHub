import pandas as pd
from hashlib import sha256
import flask_login

class User(flask_login.UserMixin):
    def __init__(self, username, password):
        # userid is the hashed username
        self.username = username
        self.password = password
        self.id = sha256(username.encode('utf-8')).hexdigest()
