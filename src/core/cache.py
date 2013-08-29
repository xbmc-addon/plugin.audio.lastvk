# -*- coding: utf-8 -*-

import xbmcup.app
import api

class ClearCache(xbmcup.app.Handler):
    def handle(self):
        if self.argv and isinstance(self.argv, dict) and 'site' in self.argv:
            if self.argv['site'] == 'lastfm':
                api.cache.flush()
                xbmcup.gui.alert(u'Кэш для Last.fm сброшен.', title='Last.fm')

            elif self.argv['site'] == 'vk':
                xbmcup.gui.alert(u'Кэш для ВКонтакта сброшен.', title='VK')