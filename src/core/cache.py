# -*- coding: utf-8 -*-

import xbmcup.app

from api import cache, cacheVK
from language import lang

class ClearCache(xbmcup.app.Handler):
    def handle(self):
        if self.argv and isinstance(self.argv, dict) and 'site' in self.argv:
            if self.argv['site'] == 'lastfm':
                cache.flush()
                xbmcup.gui.alert(lang.cache_lastfm_empty, title='Last.fm')

            elif self.argv['site'] == 'vk':
                cacheVK.flush()
                xbmcup.gui.alert(lang.cache_vk_empty, title='VK')