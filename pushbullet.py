# -*- encoding: utf-8 -*-
from requests import session
from os.path import basename
import datetime
import json
import time

# Events {{{
class Event(object):
    '''
    Abstract Pushbullet event
    '''
    __slots__ = ['api', 'time']
    def __init__(self, api):
        self.time = time.time()
        self.api = api

    def __repr__(self):
        return '<%s @%s>' % (self.__class__.__name__, self.time)

class NopEvent(Event):
    '''
    Nop event (keep-alive ticks)
    '''
    pass

class TickleEvent(Event):
    '''
    Tickle event (user pushes)
    '''
    __slots__ = ['api', 'time', 'subtype']
    def __init__(self, api, subtype):
        Event.__init__(self, api)
        self.subtype = subtype

    def pushes(self, skip_empty=False):
        return self.api.pushes(since=self.time, skip_empty=skip_empty)

    def __repr__(self):
        return '<%s[%s] @%s>' % (self.__class__.__name__, self.subtype, self.time)

class PushEvent(Event):
    '''
    Push event (device notification mirroring)
    '''
    __slots__ = ['api', 'time', 'push']
    def __init__(self, api, push):
        Event.__init__(self, api)
        self.push = push

    def __repr__(self):
        return '<%s[%r] @%s>' % (self.__class__.__name__, self.push, self.time)

# }}}

class PushBulletError(Exception):
    pass

class PushBulletObject(object):
    @property
    def uri(self):
        raise NotImplementedError

    def delete(self):
        self.api.delete(self.uri)

# Push targets {{{

class PushTarget(PushBulletObject):
    '''
    Abstract push target object
    '''
    def __init__(self, api, iden, **data):
        self.api = api
        self.iden = iden
        self.__dict__.update(data)

    @property
    def ident(self):
        raise NotImplementedError

    def push(self, push):
        push.send(self)


class Contact(PushTarget):
    '''
    Contact to push to
    '''
    def __repr__(self):
        return '<Contact[%s]: %s <%s>>' % (self.iden, self.name, self.email)

    def __str__(self):
        return self.email

    @property
    def ident(self):
        return {'email': self.email_normalized}

    @property
    def uri(self):
        return 'contacts/%s' % self.iden


class Device(PushTarget):
    '''
    Device to push to
    '''
    def __repr__(self):
        return '<Device[%s]: %s>' % (self.iden, self.model)

    def __str__(self):
        return self.iden

    @property
    def ident(self):
        return {'device_iden': self.iden}

    @property
    def uri(self):
        return 'devices/%s' % self.iden
        
# }}}

# Pushes {{{

class Push(PushBulletObject):
    '''
    Abstract push object
    '''
    type = None
    def __init__(self, **data):
        self.__dict__.update(data)

    def send(self, target):
        data = self.data
        data.update(target.ident)
        data['type'] = self.type
        result = target.api.post('pushes', **data)
        self.api = target.api
        self.__dict__.update(result)
        
    @property
    def data(self):
        raise NotImplementedError

    def __eq__(self, other):
        return isinstance(other, Push) and self.iden == other.iden

    def __repr__(self):
        return '<%s[%s]: %s>' % (self.__class__.__name__, getattr(self, 'iden', None), str(self))

    def __str__(self):
        return '%s push' % getattr(self, 'type', 'general')

    @property
    def uri(self):
        return 'pushes/%s' % self.iden

class NotePush(Push):
    '''
    Note push
    '''
    type = 'note'
    def __init__(self, title, body, **data):
        self.title, self.body = title, body
        Push.__init__(self, **data)

    @property
    def data(self):
        return {'title': self.title, 'body': self.body}

    def __str__(self):
        return self.title

class LinkPush(Push):
    '''
    Link push
    '''
    type = 'link'
    def __init__(self, title, url, body='', **data):
        self.title, self.url, self.body = title, url, body
        Push.__init__(self, **data)

    @property
    def data(self):
        return {'title': self.title, 'url': self.url, 'body': self.body}

    def __str__(self):
        return self.url

class AddressPush(Push):
    '''
    Address push
    '''
    type = 'address'
    def __init__(self, name, address, **data):
        self.name, self.address = name, address
        Push.__init__(self, **data)

    @property
    def data(self):
        return {'name': self.name, 'address': self.address}

    def __str__(self):
        return '%s (%s)' % (self.name, self.address)

class ListPush(Push):
    '''
    List push
    '''
    type = 'list'
    def __init__(self, title, items, **data):
        self.title, self.items = title, list(items)
        Push.__init__(self, **data)

    @property
    def data(self):
        return {'title': self.title, 'items': self.items}

    def __str__(self):
        return '%s (%d)' % (self.title, len(self.items))

class FilePush(Push):
    '''
    File push
    '''
    type = 'file'
    def __init__(self, file_name, file_type='application/octet-stream', body='', **data):
        self.file_name, self.file_type = file_name, file_type
        self.body = body
        Push.__init__(self, **data)

    def send(self, target):
        with open(self.file_name, 'rb') as f:
            req = target.api.get('upload-request', file_name=basename(self.file_name), file_type=self.file_type)
            target.api.upload(req['upload_url'], data=req['data'], file=f)
            self.file_name, self.file_type, self.file_url = req['file_name'], req['file_type'], req['file_url']

        Push.send(self, target)

    @property
    def data(self):
        return {'file_name': self.file_name, 'file_type': self.file_type, 'file_url': self.file_url, 'body': self.body}

    def __str__(self):
        return self.file_name

class MirrorPush(Push):
    '''
    Mirror push (internal usage only)
    '''
    type = 'mirror'

    def send(self, target):
        raise NotImplementedError

class DismissalPush(Push):
    '''
    Dismissal push (internal usage only)
    '''
    type = 'dismissal'

    def send(self, target):
        raise NotImplementedError

# }}}

# Main API class {{{

class PushBullet(object):
    '''
    Main API class for PushBullet
    '''

    API_URL = 'https://api.pushbullet.com/v2/%s'

    def __init__(self, apikey):
        '''
        Initialize API object (get API key from https://www.pushbullet.com/account)
        '''
        self.apikey = apikey
        self.sess = session()
        self.sess.auth = (apikey, '')

    def make_push(self, push):
        '''
        Factory to create a push object out of raw data in dictionary
        '''
        pushcls = {
                'note': NotePush,
                'list': ListPush,
                'link': LinkPush,
                'file': FilePush,
                'address': AddressPush,
                'mirror': MirrorPush,
                'dismissal': DismissalPush,
                }.get(push.get('type'), Push)
        return pushcls(api=self, **push)

    def delete(self, _uri):
        '''
        Helper method for DELETE requests to API
        '''
        self.sess.delete(self.API_URL % _uri).raise_for_status()

    def post(self, _uri, **data):
        '''
        Helper method for POST requests to API
        '''
        response = self.sess.post(self.API_URL % _uri, data=json.dumps(data),
                headers={'content-type': 'application/json'})
        response.raise_for_status()

        result = response.json()

        if 'error' in result:
            raise PushBulletError(result['message'])

        return result

    def get(self, _uri, **params):
        '''
        Helper method for GET requests to API
        '''
        response = self.sess.get(self.API_URL % _uri, params=params)
        response.raise_for_status()

        result = response.json()

        if 'error' in result:
            raise PushBulletError(result['message'])

        return result

    def upload(self, _uri, data, **files):
        '''
        Helper method to upload a file to given URL
        '''
        response = self.sess.post(_uri, data=data, files=files, auth=()).raise_for_status()

    __devices = None
    def devices(self, reset_cache=False):
        '''
        Get available devices to push to
        '''
        if not reset_cache and self.__devices:
            return self.__devices

        self.__devices = map(lambda d: Device(self, **d), self.get('devices')['devices'])
        return self.__devices


    __contacts = None
    def contacts(self, reset_cache=False):
        '''
        Get available contacts to push to
        '''
        if not reset_cache and self.__contacts:
            return self.__contacts

        self.__contacts = map(lambda c: Contact(self, **c), self.get('contacts')['contacts'])
        return self.__contacts


    def pushes(self, since=0, skip_empty=True):
        '''
        Generator fetches and yields all pushes since given timestamp
        '''
        if isinstance(since, datetime.date):
            since = since.strftime('%s')
        elif isinstance(since, datetime.timedelta):
            since = (datetime.datetime.now() - since).strftime('%s')

        pushes = self.get('pushes', modified_after=since)

        while True:
            for push in pushes['pushes']:
                if skip_empty and not push.get('type'):
                    continue

                yield self.make_push(push)

            if not pushes.get('cursor'):
                break

            pushes = self.get('pushes', cursor=pushes['cursor'])

    def me(self):
        '''
        Get current user information
        '''
        return self.get('users/me')

    def push(self, target, push):
        '''
        Send push to a target
        '''
        push.send(target)

    def stream(self, skip_nop=True):
        '''
        Generator to listen for events on websocket and yield them
        '''
        from websocket import create_connection
        conn = create_connection('wss://stream.pushbullet.com/websocket/%s' % self.apikey)
        while True:
            event = json.loads(conn.recv())
            evtype = event['type']
            if skip_nop and evtype == 'nop':
                continue

            event = (NopEvent(self) if evtype == 'nop' else
                     TickleEvent(self, event['subtype']) if evtype == 'tickle' else
                     PushEvent(self, self.make_push(event['push'])) if evtype == 'push' else
                     None)
            if event:
                yield event

# }}}

#import yaml
#with open('/usr/local/etc/pushbullet.yml', 'rb') as f:
#    config = yaml.safe_load(f)
#
#pb = PushBullet(config['apikey'])

