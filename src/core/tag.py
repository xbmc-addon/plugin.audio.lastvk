# -*- coding: utf-8 -*-

import xbmcup.app

from common import RenderArtists, COVER_BACKWARD, COVER_FORWARD
from api import lastfm

class Tags(xbmcup.app.Handler, RenderArtists):
    def handle(self):
        if 'tag' not in self.argv:
            tags = [dict(name=x) for x in self.argv['tags']] if 'tags' in self.argv else lastfm.tag.getTopTags()
            for tag in tags:
                self.item(tag['name'].capitalize(), self.link('tags', tag=tag['name']), folder=True, cover=self.parent.cover, fanart=self.parent.fanart)

            self.render(mode='list')

        else:
            page = self.argv.get('page', 1)

            if page > 1:
                self.item(u'[COLOR FF0DA09E][B]Назад[/B][/COLOR]', self.replace('tags', tag=self.argv['tag'], page=page - 1), folder=True, cover=COVER_BACKWARD, fanart=self.parent.fanart)
            
            if self.render_artists(lastfm.tag.getTopArtists(tag=self.argv['tag'], limit=100, page=page)):
                self.item(u'[COLOR FF0DA09E][B]Далее[/B][/COLOR]', self.replace('tags', tag=self.argv['tag'], page=page + 1), folder=True, cover=COVER_FORWARD, fanart=self.parent.fanart)

            self.render(content='artists', mode='thumb')
