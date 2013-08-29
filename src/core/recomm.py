# -*- coding: utf-8 -*-

import xbmcup.app

from common import RenderArtists
from api import lastfm

class Recommendations(xbmcup.app.Handler, RenderArtists):
    def handle(self):
        self.render_artists(lastfm.user.getRecommendedArtists(limit=200))
        self.render(content='artists', mode='thumb')
