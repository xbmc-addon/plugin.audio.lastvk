# -*- coding: utf-8 -*-

import xbmcup.db
import xbmcup.system

from lastfm import LastFM, LastFMError
from vk import VK, VKError
from fanarttv import FanartTV, FanartTVError

cache  = xbmcup.db.Cache(xbmcup.system.fs('sandbox://lastvk.cache.db'))
lastfm = LastFM('2c207878e17c021c6ee060f8f39487f2', '570aa4c51ccb896a4130363ca55ecac2', 'plugin.audio.lastvk', 'lastfm_login', 'lastfm_password', 'lastfm_session_key')
vk     = VK('3819266', 'vk_login', 'vk_password', 'vk_token')
fanart = FanartTV('8f02185df376a8ec860a83cdeb41ca23')
