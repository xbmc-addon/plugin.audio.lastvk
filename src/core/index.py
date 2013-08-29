# -*- coding: utf-8 -*-

import xbmcup.system
import xbmcup.gui

class Index(xbmcup.app.Handler):
    def handle(self):

        cover = xbmcup.system.fs('home://addons/plugin.audio.lastvk/icon.png')
        fanart = xbmcup.system.fs('home://addons/plugin.audio.lastvk/fanart.jpg')

        self.item(u'Библиотека', self.link('library'), folder=True, cover=cover, fanart=fanart)
        self.item(u'Плейлисты', self.link('playlists'), folder=True, cover=cover, fanart=fanart)
        self.item(u'Рекомендации', self.link('recommendations'), folder=True, cover=cover, fanart=fanart)

        self.item(u'Чарты', self.link('chart'), folder=True, cover=cover, fanart=fanart)

        self.item(u'Поиск', self.link('search-lastfm'), folder=True, cover=cover, fanart=fanart)
        self.item(u'ВКонтакте', self.link('index-vk'), folder=True, cover=cover, fanart=fanart)
        
        self.render(mode='list')



class Info(xbmcup.app.Handler):
    def handle(self):
        # TODO: надо заменить на xbmcup

        import xbmc
        xbmc.executebuiltin('Action(Info)')


class Setting(xbmcup.app.Handler):
    def handle(self):
        xbmcup.gui.setting()

