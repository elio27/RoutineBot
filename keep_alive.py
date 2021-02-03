from flask import Flask
from threading import Thread

app = Flask("")

@app.route('/')
def home():
  return "A man who kills at the front is a war hero, but if he kills out of passion, is he a criminal?"

def run():
  app.run(host='0.0.0.0', port=8080)

def keep_alive():
  t = Thread(target=run)
  t.start()