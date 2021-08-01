from flask import Flask
from threading import Thread
#Flask is the web server, this is hosted by UptimeRobot
#the server will run on a different thread from our main

app = Flask('')

@app.route('/')
def home():
  return "Hello, I'm alive!"

def run():
  app.run(host = '0.0.0.0', port=8080)

def keep_alive():
  t = Thread(target = run)
  t.start()