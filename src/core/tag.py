# -*- coding: utf-8 -*-

import xbmcup.app

from common import RenderArtists, COVER_BACKWARD, COVER_FORWARD
from api import lastfm

class Tags(xbmcup.app.Handler, RenderArtists):
    def handle(self):
        page = self.argv.get('page', 1)

        if 'tag' not in self.argv:

            if 'tags' in self.argv:
                data = dict(page=0, totalPages=0, data=self.argv['tags'])
            else:
                data = lastfm.chart.getTopTags(page=page, limit=100)
                if not data:
                    dict(page=0, totalPages=0, data=[])

            if data['page'] > 1:
                self.item(u'[COLOR FF0DA09E][B]Назад[/B][/COLOR]', self.replace('tags', page=page - 1), folder=True, cover=COVER_BACKWARD)

            for tag in data['data']:
                self.item(tag.capitalize(), self.link('tags', tag=tag), folder=True, cover=self.parent.cover, fanart=self.parent.fanart)

            if data['page'] != data['totalPages']:
                self.item(u'[COLOR FF0DA09E][B]Далее[/B][/COLOR]', self.replace('tags', page=page + 1), folder=True, cover=COVER_FORWARD)

            self.render(mode='list')

        else:

            if page > 1:
                self.item(u'[COLOR FF0DA09E][B]Назад[/B][/COLOR]', self.replace('tags', tag=self.argv['tag'], page=page - 1), folder=True, cover=COVER_BACKWARD, fanart=self.parent.fanart)
            
            if self.render_artists(lastfm.tag.getTopArtists(tag=self.argv['tag'], limit=100, page=page)):
                self.item(u'[COLOR FF0DA09E][B]Далее[/B][/COLOR]', self.replace('tags', tag=self.argv['tag'], page=page + 1), folder=True, cover=COVER_FORWARD, fanart=self.parent.fanart)

            self.render(content='artists', mode='thumb')
