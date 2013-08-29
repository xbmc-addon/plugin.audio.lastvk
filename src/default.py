# -*- coding: utf-8 -*-

import xbmcup.app

# HANDLERS

from core.index     import Index, Info, Setting
from core.vkontakte import IndexVK, TracksVK
from core.chart     import Chart, ChartArtists, ChartTracks
from core.playlist  import Playlist, PlaylistAdd, PlaylistTracks
from core.library   import Library, LibraryArtists, LibraryArtist, LibraryAlbums, LibraryTracks
from core.search    import SearchLastFM, SearchVK
from core.play      import PlayVideo, PlayAudio
from core.artist    import Artist, Albums, AlbumTracks, Tracks, Similar, Bio, Videos
from core.tag       import Tags
from core.recomm    import Recommendations
from core.cache     import ClearCache


# ROUTES

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

plugin.route('chart',            Chart)
plugin.route('chart-artists',    ChartArtists)
plugin.route('chart-tracks',     ChartTracks)

plugin.route('search-lastfm',    SearchLastFM)
plugin.route('search-vk',        SearchVK)

plugin.route('tags',             Tags)
plugin.route('recommendations',  Recommendations)

plugin.route('play-video',       PlayVideo)
plugin.route('play-audio',       PlayAudio)

plugin.route('index-vk',         IndexVK)
plugin.route('tracks-vk',        TracksVK)

plugin.route('info',             Info)
plugin.route('setting',          Setting)
plugin.route('clear-cache',      ClearCache)

plugin.run()
