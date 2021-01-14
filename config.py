import os
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database


# TODO IMPLEMENT DATABASE URL
SQLALCHEMY_DATABASE_URI = 'postgres://vfnnyhaoiiyngl:f4750b9320139decf9b7069c80528bdc3e9c0b71f509f5fc070e1bc9b8d516b6@ec2-54-156-73-147.compute-1.amazonaws.com:5432/d2oll43lactub6'
SQLALCHEMY_TRACK_MODIFICATIONS = False
