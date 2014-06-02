pushbullet
==========

Python bindings for Pushbullet (http://pushbullet.com/) API v2

```python
import pushbullet as pb

API_KEY = '0123456789'

api = pb.PushBullet(API_KEY)

# you can get .devices() (or .contacts() in the same way)...
devices = api.devices()
device = devices[0]

# ...send a push to device or contact...
pb.NotePush('title', 'message').send(device)

# ...or push to device...
device.push(pb.LinkPush('title', 'http://google.com/'))

# ...or even watch for events! (requires websockets-client)
for event in api.stream():
    print(event)
```
