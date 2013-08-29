# -*- coding: utf-8 -*-

import xbmcup.app

from common import RenderArtists, COVER_BACKWARD, COVER_FORWARD, COVER_NOALBUM
from api import lastfm

class Chart(xbmcup.app.Handler):
    def handle(self):
        self.item(u'Тэги', self.link('tags', page=1), folder=True, cover=self.parent.cover, fanart=self.parent.fanart)
        self.item(u'Исполнители', self.link('chart-artists', page=1), folder=True, cover=self.parent.cover, fanart=self.parent.fanart)
        self.item(u'Композиции', self.link('chart-tracks', page=1), folder=True, cover=self.parent.cover, fanart=self.parent.fanart)
        
        self.render(mode='list')


class ChartArtists(xbmcup.app.Handler, RenderArtists):
    def handle(self):
        page = self.argv.get('page', 1)

        data = lastfm.chart.getTopArtists(limit=100, page=page)
        if data:
            
            if data['page'] > 1:
                self.item(u'[COLOR FF0DA09E][B]Назад[/B][/COLOR]', self.replace('chart-artists', page=page - 1), folder=True, cover=COVER_BACKWARD)

            self.render_artists(data['data'])
            
            if data['page'] != data['totalPages']:
                self.item(u'[COLOR FF0DA09E][B]Далее[/B][/COLOR]', self.replace('chart-artists', page=page + 1), folder=True, cover=COVER_FORWARD)
        
        self.render(content='artists', mode='thumb')


class ChartTracks(xbmcup.app.Handler):
    def handle(self):
        page = self.argv.get('page', 1)
        
        data = lastfm.chart.getTopTracks(limit=100, page=page)
        if data:
            
            if data['page'] > 1:
                self.item(u'[COLOR FF0DA09E][B]Назад[/B][/COLOR]', self.replace('chart-tracks', page=page - 1), folder=True, cover=COVER_BACKWARD)

            for i, track in enumerate(data['data']):

                title  = track['name']
                if track['artist']:
                    title = u'[B]' + track['artist'] + u'[/B]  -  ' + title

                item = dict(
                    url    = self.resolve('play-audio', artist=track['artist'], song=track['name']),
                    title  = title,
                    media  = 'audio',
                    info   = {'title': track['name']},
                    menu   = [],
                    menu_replace = True
                )

                item['menu'].append((u'Информация', self.link('info')))
                item['menu'].append((u'Добавить в плейлист', self.link('playlist-add', artist=track['artist'], song=track['name'])))
                item['menu'].append((u'Добавить в библиотеку', self.link('library-add', artist=track['artist'], track=track['name'])))
                item['menu'].append((u'Настройки дополнения', self.link('setting')))

                item['info']['artist'] = track['artist']
                item['info']['duration'] = track['duration']
                
                item['info']['tracknumber'] = i + 1 + 100*(page - 1)

                if track['image']:
                    item['cover'] = track['image']
                    item['fanart'] = track['image']
                else:
                    item['cover'] = COVER_NOALBUM

                if self.parent.fanart:
                    item['fanart'] = self.parent.fanart

                self.item(**item)



            if data['page'] != data['totalPages']:
                self.item(u'[COLOR FF0DA09E][B]Далее[/B][/COLOR]', self.replace('chart-tracks', page=page + 1), folder=True, cover=COVER_FORWARD)

        self.render(content='songs', mode='list')
