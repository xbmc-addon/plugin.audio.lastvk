# -*- coding: utf-8 -*-

import xbmcup.app

from common import RenderTracksVK
from api import vk

class IndexVK(xbmcup.app.Handler):
    def handle(self):
        self.item(u'[COLOR FF0DA09E]Поиск[/COLOR]', self.link('search-vk'), folder=True, cover=self.parent.cover, fanart=self.parent.fanart)
        self.item(u'[COLOR FF0DA09E]Мои аудиозаписи[/COLOR]', self.link('tracks-vk'), folder=True, cover=self.parent.cover, fanart=self.parent.fanart)

        result = vk.api('audio.getAlbums', count=100)
        if result and result['items']:
            for playlist in result['items']:
                self.item(playlist['title'], self.link('tracks-vk', pid=playlist['album_id']), folder=True, cover=self.parent.cover, fanart=self.parent.fanart)
        
        self.render(mode='list')


class TracksVK(xbmcup.app.Handler, RenderTracksVK):
    def handle(self):
        params = dict(count=6000)
        if self.argv and 'pid' in self.argv:
            params['album_id'] = self.argv['pid']

        result = vk.api('audio.get', **params)
        if result:
            self.render_tracks_vk(result['items'])
                
        self.render(content='songs', mode='biglist')

