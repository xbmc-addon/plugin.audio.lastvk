# -*- coding: utf-8 -*-

import xbmcup.app

from google import YouTube
from api import vk


class PlayVideo(xbmcup.app.Handler):
    def handle(self):
        return YouTube().resolve(self.argv['vid'])



class PlayAudio(xbmcup.app.Handler):
    def handle(self):
        if 'url' in self.argv:
            data = [dict(url=self.argv['url'], title=self.argv['title'], artist=self.argv['artist'], duration=self.argv['duration'])]

        else:
            result = vk.api('audio.search', q=u' - '.join([self.argv['artist'], self.argv['song']]), auto_complete=1, count=300)
            if not result or not result['items']:
                return None

            data = self.filter_one(result['items'])
            if not data:
                return None


        self.parent.path = data[0]['url']
        self.parent.info['title'] = data[0]['title']
        self.parent.info['artist'] = data[0]['artist']
        self.parent.info['duration'] = data[0]['duration']

        return self.parent


    def filter_one(self, data):
        artist = self.argv['artist'].lower()
        song = self.argv['song'].lower()
        return [x for x in data if x['artist'].lower() == artist and x['title'].lower() == song]