# -*- coding: utf-8 -*-

import xbmcup.app

from common import RenderArtists, COVER_BACKWARD, COVER_FORWARD, COVER_NOALBUM
from api import lastfm

class Library(xbmcup.app.Handler):
    def handle(self):
        self.item(u'Исполнители', self.link('library-artists', page=1), folder=True, cover=self.parent.cover, fanart=self.parent.fanart)
        self.item(u'Альбомы', self.link('library-albums', page=1), folder=True, cover=self.parent.cover, fanart=self.parent.fanart)
        self.item(u'Трэки', self.link('library-tracks', page=1), folder=True, cover=self.parent.cover, fanart=self.parent.fanart)
        
        self.render(mode='list')


class LibraryArtists(xbmcup.app.Handler, RenderArtists):
    def handle(self):
        page = self.argv.get('page', 1)

        data = lastfm.library.getArtists(limit=100, page=page)
        if data:
            
            if data['page'] > 1:
                self.item(u'[COLOR FF0DA09E][B]Назад[/B][/COLOR]', self.replace('library-artists', page=page - 1), folder=True, cover=COVER_BACKWARD)

            self.render_artists(data['data'], 'library-artist')
            
            if data['page'] != data['totalPages']:
                self.item(u'[COLOR FF0DA09E][B]Далее[/B][/COLOR]', self.replace('library-artists', page=page + 1), folder=True, cover=COVER_FORWARD)
        
        self.render(content='artists', mode='thumb')


class LibraryArtist(xbmcup.app.Handler):
    def handle(self):
        self.item(u'Композиции', self.link('library-tracks', artist=self.argv['artist']), folder=True, cover=self.parent.cover, fanart=self.parent.fanart)
        self.item(u'Альбомы', self.link('library-albums', artist=self.argv['artist']), folder=True, cover=self.parent.cover, fanart=self.parent.fanart)
        self.item(u'Профайл исполнителя', self.link('artist', mbid=self.argv['mbid'], artist=self.argv['artist']), folder=True, cover=self.parent.cover, fanart=self.parent.fanart)
        
        self.render(mode='list')



class LibraryAlbums(xbmcup.app.Handler):
    def handle(self):
        artist = self.argv.get('artist')
        page = self.argv.get('page', 1)
        
        data = lastfm.library.getAlbums(artist=artist, limit=100, page=page)
        if data:
            
            if data['page'] > 1:
                self.item(u'[COLOR FF0DA09E][B]Назад[/B][/COLOR]', self.replace('library-albums', artist=artist, page=page - 1), folder=True, cover=COVER_BACKWARD)

            for album in data['data']:

                title  = album['name']
                if not artist and album['artist']:
                    title = u'[B]' + album['artist'] + u'[/B]  -  ' + title

                item = dict(
                    url    = self.link('library-tracks', album=album['name'], artist=album['artist'] or artist),
                    title  = title,
                    folder = True,
                    menu   = [(u'Добавить альбом в плейлист', self.link('playlist-add', mbid=album['mbid'], album=album['name'], artist=album['artist'] or artist)), (u'Настройки дополнения', self.link('setting'))],
                    menu_replace = True
                )

                if album['image']:
                    item['cover'] = album['image']
                    item['fanart'] = album['image']
                else:
                    item['cover'] = COVER_NOALBUM

                if self.parent.fanart:
                    item['fanart'] = self.parent.fanart

                self.item(**item)
            
            if data['page'] != data['totalPages']:
                self.item(u'[COLOR FF0DA09E][B]Далее[/B][/COLOR]', self.replace('library-artists', artist=artist, page=page + 1), folder=True, cover=COVER_FORWARD)
        
        self.render(content='albums', mode='thumb' if artist else 'list')


class LibraryTracks(xbmcup.app.Handler):
    def handle(self):
        artist = self.argv.get('artist')
        album = self.argv.get('album')
        page = self.argv.get('page', 1)
        
        data = lastfm.library.getTracks(artist=artist, album=album, limit=100, page=page)
        if data:
            
            if data['page'] > 1:
                self.item(u'[COLOR FF0DA09E][B]Назад[/B][/COLOR]', self.replace('library-tracks', artist=artist, album=album, page=page - 1), folder=True, cover=COVER_BACKWARD)

            for i, track in enumerate(data['data']):

                title  = track['name']
                if not artist:
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
                item['menu'].append((u'Добавить трэк в плейлист', self.link('playlist-add', artist=track['artist'], song=track['name'])))
                item['menu'].append((u'Настройки дополнения', self.link('setting')))

                item['info']['artist'] = track['artist']
                item['info']['album'] = track['album']
                item['info']['duration'] = track['duration']
                
                item['info']['tracknumber'] = i + 1

                if track['image']:
                    item['cover'] = track['image']
                    item['fanart'] = track['image']
                else:
                    item['cover'] = COVER_NOALBUM

                if self.parent.fanart:
                    item['fanart'] = self.parent.fanart

                self.item(**item)



            if data['page'] != data['totalPages']:
                self.item(u'[COLOR FF0DA09E][B]Далее[/B][/COLOR]', self.replace('library-tracks', artist=artist, album=album, page=page + 1), folder=True, cover=COVER_FORWARD)

        self.render(content='songs', mode='list')


