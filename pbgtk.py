#!/usr/bin/env python2

import os
import sys
import gtk
import pynotify
import pushybullet
from multiprocessing import Process as Thread

def main():
    icon_path = os.path.realpath(os.path.join(os.path.dirname(__file__), "pushbullet.png"))

    icon = gtk.StatusIcon()
    icon.set_from_file(icon_path)
    icon.set_tooltip_text("PushBullet")
    icon.set_visible(True)
    icon.connect('activate', lambda s: gtk.main_quit())

    pynotify.init("PushBullet")

    gtk_thread = Thread(target=gtk.main)

    try:
        pb = pushybullet.PushBullet(pushybullet.get_apikey_from_config() or sys.argv[1])
    except IndexError:
        from textwrap import dedent
        print(dedent('''
            Either pass your API key as first command line argument,
            or put it into your ~/.config/pushbullet/config.ini file:

            [pushbullet]
            apikey = YOUR_API_KEY_HERE
        '''))

    def pb_watch():
        for ev in pb.stream(use_server_time=True):
            for push in ev.pushes(skip_empty=True):
                try:
                    notify = pynotify.Notification(
                            push.get('title') or "PushBullet",
                            push.get('body') or push.get('url'),
                            icon_path
                    )

                    notify.show()

                except Exception as e:
                    print(e)

    pb_thread = Thread(target=pb_watch)

    gtk_thread.start()
    pb_thread.start()

    gtk_thread.join()
    pb_thread.terminate()


if __name__ == '__main__':
    main()
