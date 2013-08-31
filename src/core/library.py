# -*- coding: utf-8 -*-

import xbmcup.app

from common import RenderArtists, COVER_BACKWARD, COVER_FORWARD, COVER_NOALBUM
from api import lastfm
from language import lang

class Library(xbmcup.app.Handler):
    def handle(self):
        self.item(lang.artists, self.link('library-artists', page=1), folder=True, cover=self.parent.cover, fanart=self.parent.fanart)
        self.item(lang.albums, self.link('library-albums', page=1), folder=True, cover=self.parent.cover, fanart=self.parent.fanart)
        self.item(lang.tracks, self.link('library-tracks', page=1), folder=True, cover=self.parent.cover, fanart=self.parent.fanart)
        
        self.render(mode='list')


class LibraryArtists(xbmcup.app.Handler, RenderArtists):
    def handle(self):
        if 'delete' in self.argv:
            lastfm.library.removeArtist(artist=self.argv['delete'])


        page = self.argv.get('page', 1)

        data = lastfm.library.getArtists(limit=100, page=page)
        if data:
            
            if data['page'] > 1:
                self.item(u'[COLOR FF0DA09E][B]' + lang.previous + u'[/B][/COLOR]', self.replace('library-artists', page=page - 1), folder=True, cover=COVER_BACKWARD)

            self.render_artists(data['data'], page=page, url='library-artist')
            
            if data['page'] != data['totalPages']:
                self.item(u'[COLOR FF0DA09E][B]' + lang.next + u'[/B][/COLOR]', self.replace('library-artists', page=page + 1), folder=True, cover=COVER_FORWARD)
        
        self.render(content='artists', mode='thumb')


class LibraryArtist(xbmcup.app.Handler):
    def handle(self):
        self.item(lang.tracks, self.link('library-tracks', artist=self.argv['artist']), folder=True, cover=self.parent.cover, fanart=self.parent.fanart)
        self.item(lang.albums, self.link('library-albums', artist=self.argv['artist']), folder=True, cover=self.parent.cover, fanart=self.parent.fanart)
        self.item(lang.profile_of_artist, self.link('artist', mbid=self.argv['mbid'], artist=self.argv['artist']), folder=True, cover=self.parent.cover, fanart=self.parent.fanart)
        
        self.render(mode='list')



class LibraryAlbums(xbmcup.app.Handler):
    def handle(self):
        if 'delete' in self.argv:
            lastfm.library.removeAlbum(artist=self.argv['delete'][0], album=self.argv['delete'][1])

        artist = self.argv.get('artist')
        page = self.argv.get('page', 1)

        data = lastfm.library.getAlbums(artist=artist, limit=100, page=page)
        if data:
            
            if data['page'] > 1:
                self.item(u'[COLOR FF0DA09E][B]' + lang.previous + u'[/B][/COLOR]', self.replace('library-albums', artist=artist, page=page - 1), folder=True, cover=COVER_BACKWARD)

            for album in data['data']:

                title  = album['name']
                if not artist and album['artist']:
                    title = u'[B]' + album['artist'] + u'[/B]  -  ' + title

                item = dict(
                    url    = self.link('library-tracks', album=album['name'], artist=album['artist'] or artist),
                    title  = title,
                    folder = True,
                    menu   = [],
                    menu_replace = True
                )

                item['menu'].append((lang.add_to_playlist, self.link('playlist-add', mbid=album['mbid'], album=album['name'], artist=album['artist'] or artist)))
                item['menu'].append((lang.remove_from_library, self.replace('library-albums', artist=artist, page=page, delete=(album['artist'] or artist, album['name']))))
                item['menu'].append((lang.settings, self.link('setting')))

                if album['image']:
                    item['cover'] = album['image']
                    item['fanart'] = album['image']
                else:
                    item['cover'] = COVER_NOALBUM

                if self.parent.fanart:
                    item['fanart'] = self.parent.fanart

                self.item(**item)
            
            if data['page'] != data['totalPages']:
                self.item(u'[COLOR FF0DA09E][B]' + lang.next + u'[/B][/COLOR]', self.replace('library-artists', artist=artist, page=page + 1), folder=True, cover=COVER_FORWARD)
        
        self.render(content='albums', mode='thumb' if artist else 'list')


class LibraryTracks(xbmcup.app.Handler):
    def handle(self):
        if 'delete' in self.argv:
            lastfm.library.removeTrack(artist=self.argv['delete'][0], track=self.argv['delete'][1])

        artist = self.argv.get('artist')
        album = self.argv.get('album')
        page = self.argv.get('page', 1)
        
        data = lastfm.library.getTracks(artist=artist, album=album, limit=100, page=page)
        if data:
            
            if data['page'] > 1:
                self.item(u'[COLOR FF0DA09E][B]' + lang.previous + u'[/B][/COLOR]', self.replace('library-tracks', artist=artist, album=album, page=page - 1), folder=True, cover=COVER_BACKWARD)

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

                item['menu'].append((lang.info, self.link('info')))
                item['menu'].append((lang.add_to_playlist, self.link('playlist-add', artist=track['artist'], song=track['name'])))
                item['menu'].append((lang.remove_from_library, self.replace('library-tracks', artist=artist, album=album, page=page, delete=(track['artist'], track['name']))))
                item['menu'].append((lang.settings, self.link('setting')))

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
                self.item(u'[COLOR FF0DA09E][B]' + lang.next + u'[/B][/COLOR]', self.replace('library-tracks', artist=artist, album=album, page=page + 1), folder=True, cover=COVER_FORWARD)

        self.render(content='songs', mode='list')


class LibraryAdd(xbmcup.app.Handler):
    def handle(self):
        artist = self.argv.get('artist')
        album = self.argv.get('album')
        track = self.argv.get('track')

        if artist and album:
            lastfm.library.addAlbum(artist=artist, album=album)
        elif artist and track:
            lastfm.library.addTrack(artist=artist, track=track)
        elif artist:
            lastfm.library.addArtist(artist=artist)

