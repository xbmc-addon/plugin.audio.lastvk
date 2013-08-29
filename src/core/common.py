# -*- coding: utf-8 -*-

import urllib
import threading
import traceback

import xbmcup.system
import xbmcup.log

import api



COVER_NOALBUM  = xbmcup.system.fs('home://addons/plugin.audio.lastvk/resources/media/icons/noalbum.jpg')
COVER_BACKWARD = xbmcup.system.fs('home://addons/plugin.audio.lastvk/resources/media/icons/backward.png')
COVER_FORWARD  = xbmcup.system.fs('home://addons/plugin.audio.lastvk/resources/media/icons/forward.png')
COVER_ADD      = xbmcup.system.fs('home://addons/plugin.audio.lastvk/resources/media/icons/add.png')



class CacheLastFM:
    def encode(self, text):
        return str(urllib.quote(text.encode('utf8')))

    def cache_lastfm(self, token, method, **kwargs):
        data = api.cache.get(token)[token]
        if data:
            return data
        try:
            data = method(**kwargs)
        except:
            xbmcup.log.error(traceback.format_exc())
            return []

        if data:
            api.cache.set(token, data, 2592000) # 1 month

        return data



class RenderArtists:

    def get_fanart(self, mbids):
        
        def fetch(mbid):
            try:
                bg = api.fanart.api('artist', mbid, 'artistbackground')
            except core.fanarttv.FanartTVError:
                response['fanarttv:artist:' + mbid] = ''
            else:
                if bg:
                    response['fanarttv:artist:' + mbid] = bg
                else:
                    response['fanarttv:artist:' + mbid] = ''

        if not isinstance(mbids, (list, tuple)):
            mbids = [mbids]

        tokens = ['fanarttv:artist:' + x for x in mbids]

        result = api.cache.get(tokens)

        request = [x.split(':')[2] for x, y in result.iteritems() if not y]
        if request:

            response, pool = {}, []

            for mbid in request:
                pool.append(threading.Thread(target=fetch, args=(mbid,)))

            for t in pool:
                t.start()

            for t in pool:
                t.join()

            for token, data in response.iteritems():
                api.cache.set(token, data, 2592000) # 1 month

            result.update(response)

        # готовим финальный результат
        return dict([(x, result['fanarttv:artist:' + x]) for x in mbids])


    def render_artists(self, artists, url=None):
        if not url:
            url = 'artist'

        fanart = self.get_fanart([x['mbid'] for x in artists if x['mbid']])

        for artist in artists:

            item = dict(
                url    = self.link(url, mbid=artist['mbid'], artist=artist['name']),
                title  = artist['name'],
                folder = True,
                menu   = [(u'Настройки дополнения', self.link('setting'))],
                menu_replace = True
            )

            if artist['image']:
                item['cover'] = artist['image']
                item['fanart'] = artist['image']

            if artist['mbid'] and fanart[artist['mbid']]:
                item['fanart'] = fanart[artist['mbid']]

            self.item(**item)

        return len(artists)


class RenderTracksVK:
    def render_tracks_vk(self, data):
        total = len(data)

        use_artist = bool(len(dict([(x['artist'], 1) for x in data])) > 1)

        for i, r in enumerate(data):

            r['artist'] = r['artist'].replace('&amp;', '&')
            r['title']  =  r['title'].replace('&amp;', '&')

            title = r['title']
            if use_artist:
                title  = u'[B]' + r['artist'] + u'[/B]  -  ' + title

            item = dict(
                url    = self.resolve('play-audio', url=r['url'], artist=r['artist'], title=r['title'], duration=r['duration']),
                title  = title,
                media  = 'audio',
                info   = {'title': r['title']},
                total  = total,
                cover  = self.parent.cover,
                fanart = self.parent.fanart,
                menu   = [(u'Информация', self.link('info')), (u'Настройки дополнения', self.link('setting'))],
                menu_replace = True
            )

            item['info']['artist'] = r['artist']
            item['info']['duration'] = r['duration']
            
            item['info']['tracknumber'] = i + 1

            self.item(**item)

