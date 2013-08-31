# -*- coding: utf-8 -*-

import xbmcup.app
import xbmcup.gui

from common import CacheLastFM, COVER_NOALBUM, COVER_ADD
from api import lastfm
from language import lang


class BasePlaylist(xbmcup.app.Handler):
    def playlist_create(self):
        title = xbmcup.gui.prompt(lang.name_of_playlist)
        return lastfm.playlist.create(title) if title else None

    def playlist_add(self, data, pid=None):
        playlists = [(x['id'], x['title']) for x in lastfm.user.getPlaylists() if x['id'] != pid]
        playlists.append(('create', u'[COLOR FF0DA09E]' + lang.create_playlist + u'[/COLOR]'))
        playlist = xbmcup.gui.select(lang.select_playlist, playlists)
        if playlist == 'create':
            playlist = self.playlist_create()
        if playlist:
            for track in data:
                lastfm.playlist.addTrack(playlist, track['song'], track['artist'])


class Playlist(BasePlaylist):
    def handle(self):
        if self.argv and 'create' in self.argv:
            self.playlist_create()

        for playlist in lastfm.user.getPlaylists():

            item = dict(
                title  = playlist['title'],
                url    = self.link('playlist-tracks', pid=playlist['id']),
                folder = True,
                cover  = playlist['image'] or COVER_NOALBUM,
                fanart = self.parent.fanart
            )

            self.item(**item)

        self.item(u'[COLOR FF0DA09E]' + lang.create_playlist + u'[/COLOR]', self.replace('playlists', create=1), folder=True, cover=COVER_ADD, fanart=self.parent.fanart)
        
        self.render(mode='list')


class PlaylistAdd(BasePlaylist, CacheLastFM):
    def handle(self):
        artist = self.argv['artist']

        if 'song' in self.argv:
            self.playlist_add([dict(song=self.argv['song'], artist=artist)], pid=self.argv.get('pid'))
        else:
            mbid = self.argv['mbid']
            album = self.argv['album']

            data = self.cache_lastfm('lastfm:album:' + mbid + ':' + self.encode(album) + ':' + self.encode(artist), lastfm.album.getInfo, mbid=mbid, artist=artist, album=album)
            if data and data['tracks']:
                self.playlist_add([dict(artist=artist, song=x['name']) for x in data['tracks']])


class PlaylistTracks(xbmcup.app.Handler):
    def handle(self):
        data = lastfm.playlist.fetch(self.argv['pid'])
        if data:
            
            use_artist = bool(len(dict([(x['artist'], 1) for x in data if x['artist']])) > 1)

            for i, track in enumerate(data):
                item = dict(
                    url    = self.resolve('play-audio', artist=track['artist'], song=track['name']),
                    title  = track['name'],
                    media  = 'audio',
                    info   = {'title': track['name']},
                    menu   = [],
                    menu_replace = True
                )

                item['menu'].append((lang.info, self.link('info')))
                item['menu'].append((lang.copy_to_playlist, self.link('playlist-add', artist=track['artist'], song=track['name'], pid=self.argv['pid'])))
                item['menu'].append((lang.settings, self.link('setting')))

                item['title'] = track['name']
                if use_artist and track['artist']:
                    item['title'] = u'[B]' + track['artist'] + '[/B]  -  ' + item['title']
                    

                item['info']['artist'] = track['artist']
                item['info']['album'] = track['album']
                item['info']['duration'] = track['duration']

                item['info']['tracknumber'] = i + 1

                if track['image']:
                    item['cover'] = track['image']
                    item['fanart'] = track['image']
                else:
                    item['cover'] = COVER_NOALBUM

                self.item(**item)

        self.render(content='songs', mode='list')

