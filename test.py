#!/usr/bin/env python2

import pushybullet as pb
import sys
import time
from StringIO import StringIO

try:
    APIKEY = sys.argv[1]
except IndexError:
    print('Please provide API key for tests as the first argument')
    sys.exit(0)

# Monkey patch to delete push on cleanup
def push_delete(self):
    try:
        self.delete()
    except:
        pass
pb.Push.__del__ = push_delete

tests_started = time.time()

api = pb.PushBullet(APIKEY)

devices = api.devices()
contacts = api.contacts()
me = api.me()
chrome = api['Chrome']
device = api.create_device('Test Stream Device')

push = pb.NotePush('lorem ipsum dolor set amet', title='test note')

# Pushing via API object
api.push(push)               # push object to all devices
api.push(push, device)       # push object to device object
api.push(push, device.iden)  # push object to device iden
api.push('lorem ipsum dolor set amet', device.iden, title='test note')  # text/args to device iden

# Pusing via device object
device.push(push)  # push object
device.push('lorem ipsum dolor set amet', title='test note')  # text/args

# Sending push object itself
push.send(api)          # to API object
push.send(device)       # to device object
push.send(device.iden)  # to device iden

# Deleting push
push.delete()

# List push
push = pb.ListPush(['one', 'two', 'three'])
device.push(push)  # push list
device.push(['one', 'two', 'three'])  # push list (implicit object)
device.push(['one', 'two', 'three'], type='note')  # push list as a note
push.delete()

# File push
s = "lorem ipsum dolor set amet"
push = pb.FilePush(buffer(s), file_type="text/plain", file_name='note.txt')
device.push(push)  # push file
device.push(StringIO(s), file_name='note.txt')  # push file (implicit object)
device.push(StringIO(s), file_name='note.txt', type='note')  # push file as a note
device.push(StringIO(s), file_name='note.txt', file_type='application/octet-stream')  # push file with custom parameters
push.delete()

# Implicit link push
chrome.push('https://github.com/kstep/pushybullet')

# Deleting device
device.delete()

# Deleting test pushes
pushes = api.pushes(since=tests_started)
for push in pushes:
    push.delete()

print('OK!')
