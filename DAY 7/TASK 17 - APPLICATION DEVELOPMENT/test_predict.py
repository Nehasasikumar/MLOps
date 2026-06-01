import json
import urllib.request

url = 'http://127.0.0.1:5000/predict'
data = json.dumps({'text': 'sample test input for anomaly model'}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        print('STATUS', resp.status)
        print(resp.read().decode())
except Exception as e:
    print('ERROR', repr(e))
