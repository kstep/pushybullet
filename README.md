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
# or create device yourself (if you know device iden):
#device = pb.Device(api, 'deviden')

# ...send a push to device or contact...
pb.NotePush('title', 'message').send(device)

# ...or push to device...
device.push(pb.LinkPush('title', 'http://google.com/'))

# ...or you can take a shortcut if you are in a hurry...
api.push('deviceiden', type='note', title='title', body='message')
device.push(type='address', name='My home', address='Washington, DC')

# ...and then watch for events! (requires websockets-client)
# (warning! infinite loop here!)
for event in api.stream():
    print(event)
    
# you can iterate over all pushes (paging is handled transparently for you)
for push in api.pushes(since=-86400):  # since 1 day ago, also supports int timestamps, date and datetime objects
    print(push)
    
# and of cause you can delete pretty much anythings:
#push.delete()
#contact.delete()
#device.delete()

# note: you can delete push only if it's bound to API object
# (which is not the case by default)
# pushes are autobound to API after successful push,
# pushes fetched with `api.push()` are also already bound to the originating API,
# or you can call push.bind(api) (or api.bind(push)) explicitly:
#push.bind(api).delete()
    
```
