# -*- coding: utf-8 -*-

import xbmcup.app
import xbmcup.parser

from common import CacheLastFM, RenderArtists, COVER_NOALBUM
from api import cache, lastfm


class Base(xbmcup.app.Handler, CacheLastFM):
    def http_fetch(self, url):
        try:
            response = xbmcup.net.http.get(url)
        except xbmcup.net.http.exceptions.RequestException:
            return None
        else:
            return response.text if response.status_code == 200 else None


    
class GetArtist(Base):
    def get_artist(self, mbid, artist):
        token = 'lastfm:artist:profile:' + mbid + ':' + self.encode(artist)

        data = cache.get(token)[token]
        if data:
            return data

        data = lastfm.artist.getInfo(mbid=mbid, artist=artist)
        if data:

            for tag in ('summary', 'content'):
                if data[tag]:
                    r = data[tag].rfind('<a href="')
                    if r != -1:
                        data[tag] = data[tag][:r]
                    text = xbmcup.parser.clear.text(data[tag])
                    data[tag] = text if text else None

            cache.set(token, data, 2592000) # 1 month

        return data


class GetSimilar(Base):
    def get_similar(self, mbid, artist):
        return self.cache_lastfm('lastfm:artist:similar:' + mbid + ':' + self.encode(artist), lastfm.artist.getSimilar, mbid=mbid, artist=artist)


class GetAlbums(Base):
    def get_albums(self, mbid, artist):
        return self.cache_lastfm('lastfm:artist:albums:' + mbid + ':' + self.encode(artist), lastfm.artist.getTopAlbums, mbid=mbid, artist=artist, limit=10000)


class GetVideos(Base):
    def get_videos(self, mbid, artist, url, check=False):
        token = 'lastfm:artist:videos:' + mbid + ':' + self.encode(artist)

        videos = cache.get(token)[token]
        if videos:
            return videos

        page, videos = 1, []

        while page:
            html = self.http_fetch(url + '/+videos?page=' + str(page))
            if html is None:
                break

            box = xbmcup.parser.re('restypeclass="externalvideo"(.+?)</ul>', html)
            if not box or not box[0]:
                break

            for row in xbmcup.parser.re.all('<li(.+?)</li>', box[0]):
                href = xbmcup.parser.re('<a href="[^"]+\-([^"]+)"', row[0])
                if href and href[0]:

                    img = xbmcup.parser.re('<img src="([^"]+)"', row[0])
                    if img and img[0]:
                        img = img[0].split('/')
                        img[-1] = '0.jpg'

                        title = xbmcup.parser.re('title="([^"]+)"', row[0])
                        if title and title[0]:
                            videos.append({'id': href[0], 'image': '/'.join(img), 'title': title[0]})
                        else:
                            videos.append({'id': href[0], 'image': '/'.join(img), 'title': None})

            if check:
                break

            pages = xbmcup.parser.re('<a href="[^"]+page=([0-9]+)"[^>]+title="Next page"', html)
            if pages and pages[0]:
                page = int(pages[0])
            else:
                page = None

        else:
            if videos:
                cache.set(token, videos, 2592000) # 1 month

        return videos



class Artist(GetArtist, GetAlbums, GetVideos, GetSimilar):
    def handle(self):
        mbid = self.argv['mbid']
        artist = self.argv['artist']

        profile = self.get_artist(mbid, artist)
        if profile:

            self.item(u'Композиции', self.link('tracks', mbid=mbid, artist=artist, tags=profile['tags']), folder=True, cover=profile['image'], fanart=self.parent.fanart)

            albums = self.get_albums(mbid, artist)
            if albums:
                cover = [x['image'] for x in albums if x['image']]
                self.item(u'Альбомы', self.link('albums', mbid=mbid, artist=artist, tags=profile['tags']), folder=True, cover=(cover[0] if cover else None), fanart=self.parent.fanart)

            videos = self.get_videos(mbid, artist, profile['url'], True)
            if videos:
                self.item(u'Видеоклипы', self.link('videos', mbid=mbid, artist=artist, url=profile['url']), folder=True, cover=videos[0]['image'], fanart=self.parent.fanart)


            #self.item(u'Фотографии', self.link('images', artist=aid), folder=True, fanart=self.parent.fanart)


            if profile['tags']:
                self.item(u'Тэги', self.link('tags', tags=profile['tags']), folder=True, cover=profile['image'], fanart=self.parent.fanart)


            if profile['bio'] or profile['content'] or profile['summary']:
                self.item(u'Биография', self.link('bio', mbid=mbid, artist=artist), folder=True, cover=profile['image'], fanart=self.parent.fanart)


            if profile['has_similar']:
                similar = self.get_similar(mbid, artist)
                if similar:
                    cover = [x['image'] for x in similar if x['image']]
                    self.item(u'Похожие исполнители', self.link('similar', mbid=mbid, artist=artist), folder=True, cover=(cover[0] if cover else None), fanart=self.parent.fanart)

        self.render(content='artists', mode='list')


class Albums(GetAlbums):
    def handle(self):
        for album in [x for x in self.get_albums(self.argv['mbid'], self.argv['artist']) if x]:

            item = dict(
                url    = self.link('album-tracks', mbid=album['mbid'], album=album['name'], artist=self.argv['artist'], tags=self.argv['tags']),
                title  = album['name'],
                folder = True,
                menu   = [],
                menu_replace = True
            )

            item['menu'].append((u'Добавить в плейлист', self.link('playlist-add', mbid=album['mbid'], album=album['name'], artist=self.argv['artist'])))
            item['menu'].append((u'Добавить в библиотеку', self.link('library-add', artist=self.argv['artist'], album=album['name'])))
            item['menu'].append((u'Настройки дополнения', self.link('setting')))

            if album['image']:
                item['cover'] = album['image']
                item['fanart'] = album['image']
            else:
                item['cover'] = COVER_NOALBUM

            if self.parent.fanart:
                item['fanart'] = self.parent.fanart

            self.item(**item)

        self.render(content='albums', mode='thumb')


class AlbumTracks(Base):
    def handle(self):
        mbid = self.argv['mbid']
        album = self.argv['album']
        artist = self.argv['artist']

        data = self.cache_lastfm('lastfm:album:' + mbid + ':' + self.encode(album) + ':' + self.encode(artist), lastfm.album.getInfo, mbid=mbid, artist=artist, album=album)
        if data:
            for i, track in enumerate(data['tracks']):

                item = dict(
                    url    = self.resolve('play-audio', artist=artist, song=track['name']),
                    title  = track['name'],
                    media  = 'audio',
                    info   = {'title': track['name']},
                    menu   = [],
                    menu_replace = True
                )

                item['menu'].append((u'Информация', self.link('info')))
                item['menu'].append((u'Добавить в плейлист', self.link('playlist-add', artist=artist, song=track['name'])))
                item['menu'].append((u'Добавить в библиотеку', self.link('library-add', artist=artist, track=track['name'])))
                item['menu'].append((u'Настройки дополнения', self.link('setting')))


                item['info']['artist'] = artist
                item['info']['album'] = data['name']
                item['info']['duration'] = track['duration']
                
                if data['tags']:
                    item['info']['genre'] = u', '.join([x.capitalize() for x in data['tags']])
                elif self.argv['tags']:
                    item['info']['genre'] = u', '.join([x.capitalize() for x in self.argv['tags']])

                if data['release']:
                    item['info']['year'] = int(data['release'].split('.')[-1])

                item['info']['tracknumber'] = i + 1

                if data['image']:
                    item['cover'] = data['image']
                    item['fanart'] = data['image']
                else:
                    item['cover'] = COVER_NOALBUM

                if self.parent.fanart:
                    item['fanart'] = self.parent.fanart

                self.item(**item)

        self.render(content='songs', mode='list')


class Tracks(Base):
    def handle(self):
        mbid = self.argv['mbid']
        artist = self.argv['artist']

        tracks = self.cache_lastfm('lastfm:artist:tracks:' + mbid + ':' + self.encode(artist), lastfm.artist.getTopTracks, mbid=mbid, artist=artist, limit=200)
        if tracks:
            for i, track in enumerate(tracks):

                item = dict(
                    url    = self.resolve('play-audio', artist=(track['artist']['name'] if track['artist'] else artist), song=track['name']),
                    title  = track['name'],
                    media  = 'audio',
                    info   = {'title': track['name']},
                    menu   = [],
                    menu_replace = True
                )

                item['menu'].append((u'Информация', self.link('info')))
                item['menu'].append((u'Добавить в плейлист', self.link('playlist-add', artist=(track['artist']['name'] if track['artist'] else artist), song=track['name'])))
                item['menu'].append((u'Добавить в библиотеку', self.link('library-add', artist=(track['artist']['name'] if track['artist'] else artist), track=track['name'])))
                item['menu'].append((u'Настройки дополнения', self.link('setting')))

                item['info']['artist'] = track['artist']['name'] if track['artist'] else self.argv['artist']
                item['info']['duration'] = track['duration']
                
                if self.argv['tags']:
                    item['info']['genre'] = u', '.join([x.capitalize() for x in self.argv['tags']])

                item['info']['tracknumber'] = i + 1

                if track['image']:
                    item['cover'] = track['image']
                    item['fanart'] = track['image']
                else:
                    item['cover'] = COVER_NOALBUM

                if self.parent.fanart:
                    item['fanart'] = self.parent.fanart

                self.item(**item)

        self.render(content='songs', mode='list')



class Similar(GetSimilar, RenderArtists):
    def handle(self):
        self.render_artists(self.get_similar(self.argv['mbid'], self.argv['artist']))
        self.render(content='artists', mode='thumb')


class Bio(GetArtist):
    def handle(self):
        profile = self.get_artist(self.argv['mbid'], self.argv['artist'])
        if not profile:
            self._fail()
        else:

            text = None
            if profile['bio']:
                text = self._get_bio(profile['bio'])

            if not text:
                text = profile['content']

            if not text:
                text = profile['summary']

            if not text:
                self._fail(profile['name'])
            else:

                head = u''
                if profile['place']:
                    head = profile['place']

                if profile['formation']:
                    formations = []
                    for formation in profile['formation']:
                        if not formation['from']:
                            formations.append(u'? - ' + formation['to'])
                        elif not formation['to']:
                            formations.append(formation['from'] + u' – по сей день')
                        else:
                            formations.append(formation['from'] + u' – ' + formation['to'])

                    if formations:
                        if head:
                            head += u'  (' + u',  '.join(formations) + u')'
                        else:
                            head = u',  '.join(formations)

                if head:
                    text = u'[B]' + head + u'[/B]\n\n' + text

                xbmcup.gui.text(profile['name'], text)


    def _fail(self, title=None):
        if not title:
            title = u'Biography'
        xbmcup.gui.alert(u'Не удалось найти биографию.', title=title)

    def _get_bio(self, url):
        #html = self.http_fetch(profile['bio'])

        html = self.http_fetch(url.replace('last.fm', 'lastfm.ru'))

        if html is not None:
            box = xbmcup.parser.re('<div id="wiki">(.+?)</div>', html)
            if not box or not box[0]:
                return None
            else:
                text = box[0]
                for f, t in (('<strong>', '[B]'), ('</strong>', '[/B]'), ('\r', ''), ('\n', ''), ('<br />', '[BR]')):
                    text = text.replace(f, t)
                return xbmcup.parser.clear.text(text).replace('[BR]', '\n').strip()



class Videos(GetVideos):
    def handle(self):
        for video in self.get_videos(self.argv['mbid'], self.argv['artist'], self.argv['url']):
            title = video['title'] or u'NoName'
            self.item(title, self.resolve('play-video', vid=video['id']), cover=video['image'], fanart=self.parent.fanart)
            
        self.render(content='musicvideos', mode='thumb')


