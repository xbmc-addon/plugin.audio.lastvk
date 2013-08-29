# -*- coding: utf-8 -*-

import urllib

import xbmcup.app

from google import YouTube
from api import vk, cacheVK


class PlayVideo(xbmcup.app.Handler):
    def handle(self):
        return YouTube().resolve(self.argv['vid'])



class PlayAudio(xbmcup.app.Handler):
    def handle(self):
        if 'url' in self.argv:
            data = [dict(url=self.argv['url'], title=self.argv['title'], artist=self.argv['artist'], duration=self.argv['duration'])]

        else:
            token = str(':'.join([urllib.quote(self.argv['artist'].lower().encode('utf8')), urllib.quote(self.argv['song'].lower().encode('utf8'))]))
            
            data = self._get_cache(token)
            if not data:

                result = vk.api('audio.search', q=u' - '.join([self.argv['artist'], self.argv['song']]), auto_complete=1, count=300)
                if not result or not result['items']:
                    return None

                data = self.filter(result['items'])
                if not data:
                    return None
                
                cacheVK.set(token, '_'.join([str(data[0]['owner_id']), str(data[0]['id'])]))


        self.parent.path = data[0]['url']
        self.parent.info['title'] = data[0]['title']
        self.parent.info['artist'] = data[0]['artist']
        self.parent.info['duration'] = data[0]['duration']

        return self.parent


    def filter(self, data):
        return self.filter_one(data)


    def filter_one(self, data):
        artist = self.argv['artist'].lower()
        song = self.argv['song'].lower()
        return [x for x in data if x['artist'].lower() == artist and x['title'].lower() == song]


    def _get_cache(self, token):
        aid = cacheVK.get(token)[token]
        if not aid:
            return None
        
        result = vk.api('audio.getById', audios=aid)
        if result:
            return result[0:1]
        