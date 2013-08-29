# -*- coding: utf-8 -*-

import xbmcup.app
import xbmcup.system


# HANDLERS
from core.playlist  import Playlist, PlaylistAdd, PlaylistTracks
from core.library   import Library, LibraryArtists, LibraryArtist, LibraryAlbums, LibraryTracks
from core.search    import SearchLastFM, SearchVK
from core.play      import PlayVideo, PlayAudio
from core.artist    import Artist, Albums, AlbumTracks, Tracks, Similar, Bio, Videos
from core.tag       import Tags
from core.recomm    import Recommendations
from core.cache     import ClearCache



class Index(xbmcup.app.Handler):
    def handle(self):

        cover = xbmcup.system.fs('home://addons/plugin.audio.lastvk/icon.png')
        fanart = xbmcup.system.fs('home://addons/plugin.audio.lastvk/fanart.jpg')

        self.item(u'Библиотека', self.link('library'), folder=True, cover=cover, fanart=fanart)
        self.item(u'Плейлисты', self.link('playlists', {}), folder=True, cover=cover, fanart=fanart)
        self.item(u'Рекомендации', self.link('recommendations'), folder=True, cover=cover, fanart=fanart)

        self.item(u'Тэги', self.link('tags', {}), folder=True, cover=cover, fanart=fanart)

        self.item(u'Поиск Last.fm', self.link('search-lastfm'), folder=True, cover=cover, fanart=fanart)
        self.item(u'Поиск ВКонтакте', self.link('search-vk'), folder=True, cover=cover, fanart=fanart)
        
        self.render(mode='list')



class Info(xbmcup.app.Handler):
    def handle(self):
        # TODO: надо заменить на xbmcup

        import xbmc
        xbmc.executebuiltin('Action(Info)')


class Setting(xbmcup.app.Handler):
    def handle(self):
        xbmcup.gui.setting()



plugin = xbmcup.app.Plugin()

plugin.route( None,              Index)

plugin.route('artist',           Artist)
plugin.route('albums',           Albums)
plugin.route('album-tracks',     AlbumTracks)
plugin.route('similar',          Similar)
plugin.route('bio',              Bio)
plugin.route('videos',           Videos)
plugin.route('tracks',           Tracks)

plugin.route('library',          Library)
plugin.route('library-artists',  LibraryArtists)
plugin.route('library-artist',   LibraryArtist)
plugin.route('library-albums',   LibraryAlbums)
plugin.route('library-tracks',   LibraryTracks)

plugin.route('playlists',        Playlist)
plugin.route('playlist-add',     PlaylistAdd)
plugin.route('playlist-tracks',  PlaylistTracks)

plugin.route('search-lastfm',    SearchLastFM)
plugin.route('search-vk',        SearchVK)

plugin.route('tags',             Tags)
plugin.route('recommendations',  Recommendations)

plugin.route('play-video',       PlayVideo)
plugin.route('play-audio',       PlayAudio)

plugin.route('info',             Info)
plugin.route('setting',          Setting)
plugin.route('clear-cache',      ClearCache)

plugin.run()
