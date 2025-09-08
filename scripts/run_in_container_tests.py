#!/usr/bin/env python3
import http.client
import json

def post(body):
    conn = http.client.HTTPConnection('localhost',8000)
    conn.request('POST','/ask', body=json.dumps(body), headers={'Content-Type':'application/json'})
    r = conn.getresponse()
    data = r.read().decode()
    conn.close()
    try:
        return json.loads(data)
    except Exception:
        return {'raw': data}

out = {'flows': []}

# Flow 1
r1 = post({'question':'Ik zoek een nieuwe printer'})
pid = r1.get('pending_id')
r2 = post({'pending_id': pid, 'message':'Maximaal 200€'})
r3 = post({'pending_id': pid, 'message':'Brother'})
r4 = post({'pending_id': pid, 'message':'laser'})
out['flows'].append({'flow1':[r1, r2, r3, r4]})

# Flow 2
r = post({'question':'Ik zoek mijn mama'})
out['flows'].append({'flow2': r})

# Flow 3
r1 = post({'question':'Ik wil graag meer informatie over een Brother laserprinter'})
pid2 = r1.get('pending_id')
r2 = post({'pending_id': pid2, 'message':'Minder dan 50€'})
out['flows'].append({'flow3':[r1, r2]})

# Flow 4
r1 = post({'question':'Ik zoek een nieuwe printer'})
pid3 = r1.get('pending_id')
r2 = post({'pending_id': pid3, 'message':'Weet ik niet'})
r3 = post({'pending_id': pid3, 'message':'Weet ik niet'})
r4 = post({'pending_id': pid3, 'message':'Weet ik niet'})
r5 = post({'pending_id': pid3, 'message':'Gesorteerd op prijs'})
out['flows'].append({'flow4':[r1, r2, r3, r4, r5]})

with open('/app/pixie_test_output.json','w', encoding='utf-8') as f:
    f.write(json.dumps(out, ensure_ascii=False, indent=2))
print('Wrote /app/pixie_test_output.json')
