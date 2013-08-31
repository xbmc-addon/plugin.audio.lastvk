# -*- coding: utf-8 -*-

import xbmcup.gui

from common import RenderArtists, RenderTracksVK, COVER_NOALBUM
from api import lastfm, vk
from language import lang

class SearchLastFM(xbmcup.app.Handler, RenderArtists):
    def handle(self):
        sources = [('artist', lang.artists), ('album', lang.albums), ('track', lang.tracks), ('tag', lang.tags)]
        source = xbmcup.gui.select(lang.what_search, sources)
        if source is None:
            self.render()
        else:
            query = xbmcup.gui.prompt([x[1] for x in sources if x[0] == source][0])
            if not query:
                self.render()
            else:
                if source == 'artist':
                    self.search_artist(query)
                elif source == 'album':
                    self.search_album(query)
                elif source == 'track':
                    self.search_track(query)
                else:
                    self.search_tag(query)


    def search_artist(self, query):
        self.render_artists(lastfm.artist.search(artist=query, limit=200))
        self.render(content='artists', mode='thumb')


    def search_album(self, query):
        for album in lastfm.album.search(query, limit=200):

            title = album['name']
            if album['artist']:
                title = u'[B]' + album['artist'] + '[/B]  -  ' + title

            item = dict(
                url    = self.link('tracks', mbid=album['mbid'], name=album['name'], artist=album['artist'], tags=[], fromalbum=1),
                title  = title,
                folder = True,
                menu   = [],
                menu_replace = True
            )

            if album['artist']:
                item['menu'].append((lang.add_to_playlist, self.link('playlist-add-album', mbid=album['mbid'], name=album['name'], artist=album['artist'])))
                item['menu'].append((lang.add_to_library, self.link('library-add', artist=album['artist'], album=album['name'])))

            item['menu'].append((lang.settings, self.link('setting')))

            if album['image']:
                item['cover'] = album['image']
                item['fanart'] = album['image']
            else:
                item['cover'] = COVER_NOALBUM

            self.item(**item)

        self.render(content='albums', mode='list')


    def search_track(self, query):
        for i, track in enumerate(lastfm.track.search(track=query, limit=200)):

            item = dict(
                url    = self.resolve('play-audio', artist=track['artist'], song=track['name']),
                title  = u'[B]' + track['artist'] + '[/B]  -  ' + track['name'],
                media  = 'audio',
                info   = {'title': track['name']},
                menu   = [],
                menu_replace = True
            )

            item['menu'].append((lang.info, self.link('info')))
            item['menu'].append((lang.add_to_playlist, self.link('playlist-add', artist=track['artist'], song=track['name'])))
            item['menu'].append((lang.add_to_library, self.link('library-add', artist=track['artist'], track=track['name'])))
            item['menu'].append((lang.settings, self.link('setting')))
            
            item['info']['artist'] = track['artist']
            
            item['info']['tracknumber'] = i + 1

            if track['image']:
                item['cover'] = track['image']
                item['fanart'] = track['image']
            else:
                item['cover'] = COVER_NOALBUM

            self.item(**item)

        self.render(content='songs', mode='list')


    def search_tag(self, query):
        tags = lastfm.tag.search(tag=query, limit=200)

        for tag in tags:
            self.item(tag['name'].capitalize(), self.link('tags', tag=tag['name']), folder=True, cover=self.parent.cover)

        self.render(mode='list')



class SearchVK(xbmcup.app.Handler, RenderTracksVK):
    def handle(self):
        query = xbmcup.gui.prompt(lang.find_vkcom)
        if query:
            result = vk.api('audio.search', q=query, auto_complete=1, count=300)
            if result:
                self.render_tracks_vk(result['items'])
                
        self.render(content='songs', mode='biglist')
