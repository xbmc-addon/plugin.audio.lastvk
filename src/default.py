# -*- coding: utf-8 -*-

import urllib
import threading
import traceback

import xbmcup.app
import xbmcup.db
import xbmcup.net
import xbmcup.parser
import xbmcup.log

import core.vk
import core.lastfm
import core.fanarttv
import core.google


VK = core.vk.VK('3819266', 'vk_login', 'vk_password', 'vk_token')
LASTFM = core.lastfm.LastFM('2c207878e17c021c6ee060f8f39487f2', '570aa4c51ccb896a4130363ca55ecac2', 'plugin.audio.lastvk', 'lastfm_login', 'lastfm_password', 'lastfm_session_key')
FANARTTV = core.fanarttv.FanartTV('8f02185df376a8ec860a83cdeb41ca23')
CACHE = xbmcup.db.Cache(xbmcup.system.fs('sandbox://lastvk.cache.db'))


class Base(xbmcup.app.Handler):
    def encode(self, text):
        return str(urllib.quote(text.encode('utf8')))

    def decode(self, text):
        return urllib.unquote(str(text)).decode('utf8')

    def http_fetch(self, url):
        try:
            response = xbmcup.net.http.get(url)
        except xbmcup.net.http.exceptions.RequestException:
            return None
        else:
            return response.text if response.status_code == 200 else None


    def get_fanart(self, mbids):
        
        def api(mbid):
            try:
                bg = FANARTTV.api('artist', mbid, 'artistbackground')
            except core.fanarttv.FanartTVError:
                pass
            else:
                if bg:
                    response['fanarttv:artist:' + mbid] = bg

        if not isinstance(mbids, (list, tuple)):
            mbids = [mbids]

        tokens = ['fanarttv:artist:' + x for x in mbids]

        result = CACHE.get(tokens)

        request = [x.split(':')[2] for x, y in result.iteritems() if not y]
        if request:

            response, pool = {}, []

            for mbid in request:
                pool.append(threading.Thread(target=api, args=(mbid,)))

            for t in pool:
                t.start()

            for t in pool:
                t.join()

            for token, data in response.iteritems():
                CACHE.set(token, data, 2592000) # 1 month

            result.update(response)

        # готовим финальный результат
        return dict([(x, result['fanarttv:artist:' + x]) for x in mbids])


    def get_artist(self, mbid, artist):
        token = 'lastfm:artist:profile:' + mbid + ':' + self.encode(artist)

        data = CACHE.get(token)[token]
        if data:
            return data

        data = LASTFM.artist.getInfo(mbid=mbid, artist=artist)
        if data:

            for tag in ('summary', 'content'):
                if data[tag]:
                    r = data[tag].rfind('<a href="')
                    if r != -1:
                        data[tag] = data[tag][:r]
                    text = xbmcup.parser.clear.text(data[tag])
                    data[tag] = text if text else None

            CACHE.set(token, data, 2592000) # 1 month

        return data


    def get_album(self, mbid, album, artist):
        token = 'lastfm:album:' + mbid + ':' + self.encode(album) + ':' + self.encode(artist)

        data = CACHE.get(token)[token]
        if data:
            return data

        data = LASTFM.album.getInfo(mbid=mbid, artist=artist, album=album)
        if data:

            for tag in ('summary', 'content'):
                if data[tag]:
                    r = data[tag].rfind('User-contributed text is available under')
                    if r != -1:
                        data[tag] = data[tag][:r]
                    text = xbmcup.parser.clear.text(data[tag])
                    data[tag] = text

            CACHE.set(token, data, 2592000) # 1 month
            
        return data



    def get_similar(self, mbid, artist):
        token = 'lastfm:artist:similar:' + mbid + ':' + self.encode(artist)

        similar = CACHE.get(token)[token]
        if similar:
            return similar

        similar = LASTFM.artist.getSimilar(mbid=mbid, artist=artist)
        if similar:
            CACHE.set(token, similar, 2592000) # 1 month
            
        return similar


    def get_tracks(self, mbid, artist):
        token = 'lastfm:artist:tracks:' + mbid + ':' + self.encode(artist)

        tracks = CACHE.get(token)[token]
        if tracks:
            return tracks
        try:
            tracks = LASTFM.artist.getTopTracks(mbid=mbid, artist=artist, limit=200)
        except:
            xbmcup.log.error(traceback.format_exc())
            return []

        if tracks:
            CACHE.set(token, tracks, 2592000) # 1 month

        return tracks


    def get_albums(self, mbid, artist):
        token = 'lastfm:artist:albums:' + mbid + ':' + self.encode(artist)

        albums = CACHE.get(token)[token]
        if albums:
            return albums

        albums = LASTFM.artist.getTopAlbums(mbid=mbid, artist=artist, limit=10000)
        if albums:
            CACHE.set(token, albums, 2592000) # 1 month

        return albums


    def get_videos(self, mbid, artist, url, check=False):
        token = 'lastfm:artist:videos:' + mbid + ':' + self.encode(artist)

        videos = CACHE.get(token)[token]
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
                CACHE.set(token, videos, 2592000) # 1 month

        return videos



    def render_artists(self, artists):
        fanart = self.get_fanart([x['mbid'] for x in artists if x['mbid']])

        for artist in artists:

            print str(artist)

            item = dict(
                url    = self.link('artist', mbid=artist['mbid'], artist=artist['name']),
                title  = artist['name'],
                folder = True,
                menu   = [(u'Настройки дополнения', self.link('setting'))],
                menu_replace = True
            )

            if artist['image']:
                item['cover'] = artist['image']
                item['fanart'] = artist['image']

            if artist['mbid'] and fanart[artist['mbid']]:
                item['fanart'] = fanart[artist['mbid']]

            self.item(**item)

        return len(artists)


    

class Index(xbmcup.app.Handler):
    def handle(self):

        cover = xbmcup.system.fs('home://addons/plugin.audio.lastvk/icon.png')
        fanart = xbmcup.system.fs('home://addons/plugin.audio.lastvk/fanart.jpg')

        self.item(u'Тэги', self.link('tags', {}), folder=True, cover=cover, fanart=fanart)
        self.item(u'Рекомендации', self.link('recommendations'), folder=True, cover=cover, fanart=fanart)

        self.item(u'Поиск Last.fm', self.link('search-lastfm'), folder=True, cover=cover, fanart=fanart)
        self.item(u'Поиск ВКонтакте', self.link('search-vk'), folder=True, cover=cover, fanart=fanart)
        
        self.render(content='artists', mode='list')



class Artist(Base):
    def handle(self):
        mbid = self.argv['mbid']
        artist = self.argv['artist']

        print str([mbid, artist])

        profile = self.get_artist(mbid, artist)
        if profile:

            self.item(u'Композиции', self.link('tracks', mbid=mbid, artist=artist, tags=profile['tags'], fromtracks=1), folder=True, cover=profile['image'], fanart=self.parent.fanart)

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


class Albums(Base):
    def handle(self):
        for album in [x for x in self.get_albums(self.argv['mbid'], self.argv['artist']) if x]:

            item = dict(
                url    = self.link('tracks', mbid=album['mbid'], name=album['name'], artist=self.argv['artist'], tags=self.argv['tags'], fromalbum=1),
                title  = album['name'],
                folder = True,
                menu   = [(u'Настройки дополнения', self.link('setting'))],
                menu_replace = True
            )

            if album['image']:
                item['cover'] = album['image']
                item['fanart'] = album['image']
            else:
                item['cover'] = xbmcup.system.fs('home://addons/plugin.audio.lastvk/resources/media/icons/noalbum.jpg')

            if self.parent.fanart:
                item['fanart'] = self.parent.fanart

            self.item(**item)

        self.render(content='albums', mode='thumb')


class Tracks(Base):
    def handle(self):
        if 'fromtracks' in self.argv:
            self.render_from_tracks()
        else:
            self.render_from_album()
        self.render(content='songs', mode='list')


    def render_from_album(self):
        album = self.get_album(self.argv['mbid'], self.argv['name'], self.argv['artist'])
        if album:
            for i, track in enumerate(album['tracks']):

                item = dict(
                    url    = self.resolve('play-audio', artist=self.argv['artist'], song=track['name']),
                    title  = track['name'],
                    media  = 'audio',
                    info   = {'title': track['name']},
                    menu   = [(u'Информация', self.link('info')), (u'Настройки дополнения', self.link('setting'))],
                    menu_replace = True
                )

                item['info']['artist'] = self.argv['artist']
                item['info']['album'] = album['name']
                item['info']['duration'] = track['duration']
                
                if album['tags']:
                    item['info']['genre'] = u', '.join([x.capitalize() for x in album['tags']])
                elif self.argv['tags']:
                    item['info']['genre'] = u', '.join([x.capitalize() for x in self.argv['tags']])

                if album['release']:
                    item['info']['year'] = int(album['release'].split('.')[-1])

                item['info']['tracknumber'] = i + 1

                if album['image']:
                    item['cover'] = album['image']
                    item['fanart'] = album['image']
                else:
                    item['cover'] = xbmcup.system.fs('home://addons/plugin.audio.lastvk/resources/media/icons/noalbum.jpg')

                if self.parent.fanart:
                    item['fanart'] = self.parent.fanart

                self.item(**item)

    def render_from_tracks(self):
        for i, track in enumerate(self.get_tracks(self.argv['mbid'], self.argv['artist'])):

            item = dict(
                url    = self.resolve('play-audio', artist=(track['artist']['name'] if track['artist'] else self.argv['artist']), song=track['name']),
                title  = track['name'],
                media  = 'audio',
                info   = {'title': track['name']},
                menu   = [(u'Информация', self.link('info')), (u'Настройки дополнения', self.link('setting'))],
                menu_replace = True
            )

            item['info']['artist'] = track['artist']['name'] if track['artist'] else self.argv['artist']
            item['info']['duration'] = track['duration']
            
            if self.argv['tags']:
                item['info']['genre'] = u', '.join([x.capitalize() for x in self.argv['tags']])

            item['info']['tracknumber'] = i + 1

            if track['image']:
                item['cover'] = track['image']
                item['fanart'] = track['image']
            else:
                item['cover'] = xbmcup.system.fs('home://addons/plugin.audio.lastvk/resources/media/icons/noalbum.jpg')

            if self.parent.fanart:
                item['fanart'] = self.parent.fanart

            self.item(**item)

        



class Similar(Base):
    def handle(self):
        self.render_artists(self.get_similar(self.argv['mbid'], self.argv['artist']))
        self.render(content='artists', mode='thumb')


class Tags(Base):
    def handle(self):
        if 'tag' not in self.argv:
            tags = [dict(name=x) for x in self.argv['tags']] if 'tags' in self.argv else LASTFM.tag.getTopTags()
            for tag in tags:
                self.item(tag['name'].capitalize(), self.replace('tags', tag=tag['name']), folder=True, cover=self.parent.cover, fanart=self.parent.fanart)

            self.render(mode='list')

        else:
            page = self.argv.get('page', 1)
            tag = self.argv['tag']

            if page > 1:
                self.item(u'[COLOR FF0DA09E][B]Назад[/B][/COLOR]', self.replace('tags', tag=tag, page=page - 1), folder=True, cover=xbmcup.system.fs('home://addons/plugin.audio.lastvk/resources/media/icons/backward.png'))
            
            if self.render_artists(LASTFM.tag.getTopArtists(tag=tag, limit=100, page=page)):
                self.item(u'[COLOR FF0DA09E][B]Далее[/B][/COLOR]', self.replace('tags', tag=tag, page=page + 1), folder=True, cover=xbmcup.system.fs('home://addons/plugin.audio.lastvk/resources/media/icons/forward.png'))

            self.render(content='artists', mode='thumb')


class Bio(Base):
    def handle(self):
        mbid, artist = self.argv['mbid'], self.argv['artist']

        profile = self.get_artist(mbid, artist)
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



class Videos(Base):
    def handle(self):
        for video in self.get_videos(self.argv['mbid'], self.argv['artist'], self.argv['url']):
            title = video['title'] or u'NoName'
            self.item(title, self.resolve('play-video', vid=video['id']), cover=video['image'], fanart=self.parent.fanart)
            
        self.render(content='musicvideos', mode='thumb')



class PlayVideo(xbmcup.app.Handler):
    def handle(self):
        return core.google.YouTube().resolve(self.argv['vid'])


class PlayAudio(xbmcup.app.Handler):
    def handle(self):
        if 'url' in self.argv:
            data = [dict(url=self.argv['url'], title=self.argv['title'], artist=self.argv['artist'], duration=self.argv['duration'])]

        else:
            result = VK.api('audio.search', q=u' - '.join([self.argv['artist'], self.argv['song']]), auto_complete=1, count=300)
            if not result or not result['items']:
                return None

            data = self.filter_one(result['items'])
            if not data:
                return None


        self.parent.path = data[0]['url']
        self.parent.info['title'] = data[0]['title']
        self.parent.info['artist'] = data[0]['artist']
        self.parent.info['duration'] = data[0]['duration']

        return self.parent


    def filter_one(self, data):
        artist = self.argv['artist'].lower()
        song = self.argv['song'].lower()
        return [x for x in data if x['artist'].lower() == artist and x['title'].lower() == song]
        



class SearchLastFM(Base):
    def handle(self):
        sources = [('artist', u'Исполнители'), ('album', u'Альбомы'), ('track', u'Композиции'), ('tag', u'Теги')]
        source = xbmcup.gui.select(u'Что ищем?', sources)
        if source is None:
            self.render()
        else:
            query = xbmcup.gui.prompt([x[1] for x in sources if x[0] == source][0])
            if not query:
                self.render()
            else:
                if source == 'artist':
                    self.search_artist(query)
                elif source == 'album':
                    self.search_album(query)
                elif source == 'track':
                    self.search_track(query)
                else:
                    self.search_tag(query)


    def search_artist(self, query):
        self.render_artists(LASTFM.artist.search(artist=query, limit=200))
        self.render(content='artists', mode='thumb')


    def search_album(self, query):
        albums = LASTFM.album.search(album=query, limit=200)

        for i, album in enumerate([x for x in self.get_album(albums) if x]):
            if album:

                title = album['name']
                if albums[i]['artist']:
                    title = u'[B]' + albums[i]['artist'] + '[/B] - ' + title

                item = dict(
                    url    = self.link('tracks', mbid=album['mbid'], name=album['name'], artist=albums[i]['artist'], tags=[], fromalbum=1),
                    title  = title,
                    folder = True,
                    menu   = [(u'Настройки дополнения', self.link('setting'))],
                    menu_replace = True
                )

                if album['image']:
                    item['cover'] = album['image']
                    item['fanart'] = album['image']
                else:
                    item['cover'] = xbmcup.system.fs('home://addons/plugin.audio.lastvk/resources/media/icons/noalbum.jpg')

                self.item(**item)

        self.render(content='albums', mode='list')

    def search_track(self, query):
        for i, track in enumerate(LASTFM.track.search(track=query, limit=200)):

            item = dict(
                url    = self.resolve('play-audio', artist=track['artist'], song=track['name']),
                title  = u'[B]' + track['artist'] + '[/B] - ' + track['name'],
                media  = 'audio',
                info   = {'title': track['name']},
                menu   = [(u'Информация', self.link('info')), (u'Настройки дополнения', self.link('setting'))],
                menu_replace = True
            )

            item['info']['artist'] = track['artist']
            
            item['info']['tracknumber'] = i + 1

            if track['image']:
                item['cover'] = track['image']
                item['fanart'] = track['image']
            else:
                item['cover'] = xbmcup.system.fs('home://addons/plugin.audio.lastvk/resources/media/icons/noalbum.jpg')

            self.item(**item)

        self.render(content='songs', mode='list')

    def search_tag(self, query):
        tags = LASTFM.tag.search(tag=query, limit=200)

        for tag in tags:
            self.item(tag['name'].capitalize(), self.link('tags', tag=tag['name']), folder=True, cover=self.parent.cover)

        self.render(mode='list')



class SearchVK(xbmcup.app.Handler):
    def handle(self):
        query = xbmcup.gui.prompt(u'Поиск ВКонтакте')
        if query:
            result = VK.api('audio.search', q=query, auto_complete=1, count=300)
            if result:
                total = len(result['items'])

                for i, r in enumerate(result['items']):

                    item = dict(
                        url    = self.resolve('play-audio', url=r['url'], artist=r['artist'], title=r['title'], duration=r['duration']),
                        title  = u'[B]' + r['artist'] + u'[/B] - ' + r['title'],
                        media  = 'audio',
                        info   = {'title': r['title']},
                        menu   = [(u'Информация', self.link('info')), (u'Настройки дополнения', self.link('setting'))],
                        menu_replace = True,
                        total  = total
                    )

                    item['info']['artist'] = r['artist']
                    item['info']['duration'] = r['duration']
                    
                    item['info']['tracknumber'] = i + 1

                    self.item(**item)

        self.render(content='songs', mode='list')


class Recommendations(Base):
    def handle(self):
        self.render_artists(LASTFM.user.getRecommendedArtists(limit=200))
        self.render(content='artists', mode='thumb')




class Info(xbmcup.app.Handler):
    def handle(self):
        # TODO: надо заменить на xbmcup

        import xbmc
        xbmc.executebuiltin('Action(Info)')


class Setting(xbmcup.app.Handler):
    def handle(self):
        xbmcup.gui.setting()




plugin = xbmcup.app.Plugin()

plugin.route(  None,     Index)

plugin.route('artist', Artist)
plugin.route('albums', Albums)
plugin.route('similar', Similar)
plugin.route('tags', Tags)
plugin.route('bio', Bio)
plugin.route('videos', Videos)
plugin.route('tracks', Tracks)

plugin.route('play-video', PlayVideo)
plugin.route('play-audio', PlayAudio)

plugin.route('search-lastfm', SearchLastFM)
plugin.route('search-vk', SearchVK)

plugin.route('recommendations', Recommendations)

plugin.route('info', Info)
plugin.route('setting', Setting)

plugin.run()
