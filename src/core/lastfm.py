# -*- coding: utf-8 -*-

import re
import hashlib
import xml.etree.ElementTree as ET

import xbmcup.net
import xbmcup.app
import xbmcup.gui

AUTH_METHOD = (
    'user.getRecommendedArtists',
    'track.updateNowPlaying',
    'track.scrobble'
)


class LastFMError(Exception):
    __slots__ = ["error"]
    def __init__(self, error_data):
        self.error = error_data
        Exception.__init__(self, str(self))

    @property
    def code(self):
        return self.error['error']

    @property
    def message(self):
        return self.error['message']

    def __str__(self):
        return "Error(code = '%s', message = '%s')" % (self.code, self.message)


class _Base:
    def __init__(self, api):
        self.api = api

    def get_text_list(self, xml, path, convert=None):
        if not convert:
            convert = unicode
        return [convert(x) for x in [x.text for x in xml.findall(path)] if x]

    def compile(self, **kwargs):
        return dict([(k, v) for k, v in kwargs.iteritems() if v is not None])




class _Artist(_Base):
    def getInfo(self, mbid=None, artist=None):
        if mbid:
            xml = ET.fromstring(self.api('artist.getInfo', mbid=mbid, autocorrect=1))
        else:
            xml = ET.fromstring(self.api('artist.getInfo', artist=artist, autocorrect=1))

        name = xml.findtext('./artist/name')
        if name:
            artist = {'name': unicode(name)}

            artist['mbid'] = xml.findtext('./artist/mbid') or ''

            url = xml.findtext('./artist/url')
            artist['url'] = unicode(url) if url else None

            img = self.get_text_list(xml, './artist/image')
            artist['image'] = img[-1] if img else None

            artist['listeners'] = int(xml.findtext('./artist/stats/listeners') or 0)
            artist['playcount'] = int(xml.findtext('./artist/stats/playcount') or 0)

            artist['tags'] = self.get_text_list(xml, './artist/tags/tag/name')

            artist['has_similar'] = bool(xml.findall('./artist/similar/artist'))

            artist['members'] = []
            for member in xml.findall('./artist/bandmembers/member'):
                name = member.findtext('name')
                if name:
                    artist['members'].append({'name': unicode(name), 'from': int(member.findtext('yearfrom') or 0), 'to': int(member.findtext('yearto') or 0)})

            artist['bio'] = None
            bio = xml.find('./artist/bio/links/link')
            if bio is not None:
                bio = bio.get('href')
                if bio:
                    artist['bio'] = unicode(bio)

            placeformed = xml.findtext('./artist/bio/placeformed')
            artist['place'] = unicode(placeformed) if placeformed else None

            artist['formation'] = []
            for formation in xml.findall('./artist/bio/formationlist/formation'):
                f = formation.findtext('yearfrom') or 0
                t = formation.findtext('yearto') or 0
                if f or t:
                    artist['formation'].append({'from': f, 'to': t})

            for tag in ('summary', 'content'):
                text = xml.findtext('./artist/bio/' + tag)
                if text:
                    text = text.strip()
                artist[tag] = unicode(text) if text else None

            return artist


    def getTopTracks(self, mbid=None, artist=None, limit=None, page=None):
        params = self.compile(limit=limit, page=page, autocorrect=1)
        
        if mbid:
            params['mbid'] = mbid
        else:
            params['artist'] = artist
        
        result = []

        for xml in ET.fromstring(self.api('artist.getTopTracks', **params)).findall('./toptracks/track'):
            name = xml.findtext('name')
            if name:
                track = dict(
                    name=unicode(name),
                    duration = int(xml.findtext('./duration') or 0),
                    playcount = int(xml.findtext('./playcount') or 0),
                    listeners = int(xml.findtext('./listeners') or 0),
                    mbid = (xml.findtext('./mbid') or '')
                )

                track['artist'] = None
                artist_mbid = xml.findtext('./artist/mbid') or ''
                artist_name = xml.findtext('./artist/name')
                track['artist'] = {'id': artist_mbid, 'name': unicode(artist_name)} if artist_name else None

                img = self.get_text_list(xml, './image')
                track['image'] = img[-1] if img else None

                result.append(track)

        return result


    def getTopAlbums(self, mbid=None, artist=None, limit=None, page=None):
        params = self.compile(limit=limit, page=page, autocorrect=1)

        if mbid:
            params['mbid'] = mbid
        else:
            params['artist'] = artist
        
        result = []

        for xml in ET.fromstring(self.api('artist.getTopAlbums', **params)).findall('./topalbums/album'):
            mbid = xml.findtext('./mbid') or ''
            name = xml.findtext('./name') or ''
            artist = xml.findtext('./artist/name') or ''
            if mbid or (name and artist):
                img = self.get_text_list(xml, './image')
                result.append(dict(mbid=mbid, name=unicode(name), artist=unicode(artist), image=(img[-1] if img else None)))

        return result


    def getSimilar(self, mbid=None, artist=None, limit=None):
        params = self.compile(limit=limit, autocorrect=1)

        if mbid:
            params['mbid'] = mbid
        else:
            params['artist'] = artist
        
        result = []
        for xml in ET.fromstring(self.api('artist.getSimilar', **params)).findall('./similarartists/artist'):
            name = xml.findtext('./name')
            if name:
                img = self.get_text_list(xml, './image')
                result.append(dict(name=unicode(name), mbid=(xml.findtext('./mbid') or ''), image=(img[-1] if img else None)))
        return result


    def search(self, artist, limit=None, page=None):
        params = self.compile(limit=limit, page=page, artist=artist)

        result = []
        for xml in ET.fromstring(self.api('artist.search', **params)).findall('./results/artistmatches/artist'):
            name = xml.findtext('./name')
            if name:
                img = self.get_text_list(xml, './image')
                result.append(dict(name=unicode(name), mbid=(xml.findtext('./mbid') or ''), image=(img[-1] if img else None)))
        return result
        


class _Album(_Base):
    MONTH = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}
    RE_RELEASE = re.compile('([0-9]{1,2}) ([A-Za-z]{3}) ([0-9]{4})')

    def getInfo(self, mbid=None, artist=None, album=None):
        params = dict(autocorrect=1)
        if mbid:
            params['mbid'] = mbid
        else:
            params['artist'] = artist
            params['album'] = album

        xml = ET.fromstring(self.api('album.getInfo', **params))
        name = xml.findtext('./album/name')
        if name:
            album = {'name': unicode(name)}

            album['mbid'] = xml.findtext('./album/mbid') or ''

            img = self.get_text_list(xml, './album/image')
            album['image'] = img[-1] if img else None

            album['listeners'] = int(xml.findtext('./album/listeners') or 0)
            album['playcount'] = int(xml.findtext('./album/playcount') or 0)

            album['tags'] = self.get_text_list(xml, './album/toptags/tag/name')

            album['release'] = None
            releasedate = xml.findtext('./album/releasedate')
            if releasedate:
                release = self.RE_RELEASE.search(releasedate)
                if release:
                    album['release'] = '.'.join([release.group(1).rjust(2, '0'), self.MONTH[release.group(2)], release.group(3)])

            for tag in ('summary', 'content'):
                text = xml.findtext('./album/wiki/' + tag)
                if text:
                    text = text.strip()
                album[tag] = unicode(text) if text else None

            album['tracks'] = []
            for track in xml.findall('./album/tracks/track'):
                name = track.findtext('name')
                if name:
                    album['tracks'].append({'mbid': (track.findtext('./mbid') or ''), 'name': unicode(name), 'duration': int(track.findtext('./duration') or 0)})

            return album


    def search(self, album, limit=None, page=None):
        params = self.compile(limit=limit, page=page, album=album)

        result = []
        for xml in ET.fromstring(self.api('album.search', **params)).findall('./results/albummatches/album'):
            mbid = xml.findtext('./mbid') or ''
            name = xml.findtext('./name') or ''
            artist = xml.findtext('./artist') or ''
            if mbid or (name and artist):
                result.append(dict(mbid=mbid, name=unicode(name), artist=unicode(artist)))
        return result



class _Track(_Base):
    def search(self, track, artist=None, limit=None, page=None):
        params = self.compile(limit=limit, page=page, artist=artist, track=track)

        result = []
        for xml in ET.fromstring(self.api('track.search', **params)).findall('./results/trackmatches/track'):
            name = xml.findtext('./name')
            artist = xml.findtext('./artist')
            if name and artist:
                track = dict(name=unicode(name), artist=unicode(artist), mbid=(xml.findtext('./mbid') or ''))

                img = self.get_text_list(xml, './image')
                track['image'] = img[-1] if img else None

                result.append(track)
            
        return result

    def updateNowPlaying(self, artist, track, album=None, trackNumber=None, context=None, mbid=None, duration=None, albumArtist=None):
        params = self.compile(artist=artist, track=track, album=album, trackNumber=trackNumber, context=context, mbid=mbid, duration=duration, albumArtist=albumArtist)
        self.api('track.updateNowPlaying', **params)

    def scrobble(self, artist, track, timestamp, album=None, context=None, streamId=None, chosenByUser=None, trackNumber=None, mbid=None, albumArtist=None, duration=None):
        params = self.compile(artist=artist, track=track, timestamp=timestamp, album=album, context=context, streamId=streamId, chosenByUser=chosenByUser, trackNumber=trackNumber, mbid=mbid, albumArtist=albumArtist, duration=duration)
        self.api('track.scrobble', **params)


class _Tag(_Base):
    def getTopTags(self):
        result = []
        for tag in ET.fromstring(self.api('tag.getTopTags')).findall('./toptags/tag'):
            name = tag.findtext('name')
            if name:
                result.append(dict(name=unicode(name), count=int(tag.findtext('count') or 0)))
        return result

    def getTopArtists(self, tag, limit=None, page=None):
        params = self.compile(limit=limit, page=page, tag=tag)

        result = []
        for xml in ET.fromstring(self.api('tag.getTopArtists', **params)).findall('./topartists/artist'):
            name = xml.findtext('./name')
            if name:
                img = self.get_text_list(xml, './image')
                result.append(dict(name=unicode(name), mbid=(xml.findtext('./mbid') or ''), image=(img[-1] if img else None)))
        return result

    def search(self, tag, limit=None, page=None):
        params = self.compile(limit=limit, page=page, tag=tag)

        result = []
        for tag in ET.fromstring(self.api('tag.search', **params)).findall('./results/tagmatches/tag'):
            name = tag.findtext('name')
            if name:
                result.append(dict(name=unicode(name), count=int(tag.findtext('count') or 0)))
        return result



class _User(_Base):
    def getRecommendedArtists(self, limit=None, page=None):
        params = self.compile(limit=limit, page=page)
        
        result = []
        for xml in ET.fromstring(self.api('user.getRecommendedArtists', **params)).findall('./recommendations/artist'):
            name = xml.findtext('./name')
            if name:
                img = self.get_text_list(xml, './image')
                result.append(dict(name=unicode(name), mbid=(xml.findtext('./mbid') or ''), image=(img[-1] if img else None)))
        return result



class LastFM(object):
    RE_ERROR = re.compile('<error code="([0-9]+)">([^<]+)</error>', re.S)

    def __init__(self, api_key, secret_key, plugin, login, password, session_key):
        self._api_key = api_key
        self._secret_key = secret_key
        self._login = login
        self._password = password
        self._session_key = session_key

        self._setting = xbmcup.app.Setting(plugin)

        self.artist = _Artist(self.api)
        self.album  = _Album(self.api)
        self.track  = _Track(self.api)
        self.tag    = _Tag(self.api)
        self.user   = _User(self.api)

    
    def api(self, method, **kwargs):
        kwargs['method'] = method
        kwargs['api_key'] = self._api_key

        if method in AUTH_METHOD:
            while True:
                sk = self._session()
                if sk is None:
                    return None

                result = self._api('post', sk, **kwargs)
                if result is None:
                    xbmcup.app.setting[self._session_key] = ''
                else:
                    return result
        else:
            return self._api('get', None, **kwargs)


    def _api(self, http_method, sk, **kwargs):
        params = {}
        if sk:
            params['sk'] = sk
        params.update(kwargs)

        if http_method == 'post':
            params['api_sig'] = self._sig(params)
            response = xbmcup.net.http.post('https://ws.audioscrobbler.com/2.0/', data=params)
        else:
            response = xbmcup.net.http.get('http://ws.audioscrobbler.com/2.0/', params=params)

        if response.status_code < 200 or response.status_code > 299:
            raise LastFMError(dict(error=response.status_code, message='HTTP Error'))

        err = self.RE_ERROR.search(response.content)
        if err:
            err_code = int(err.group(1))
            if err_code in (4, 9):
                return None
            raise LastFMError(dict(error=err_code, message=err.group(2)))

        return response.content


    def _session(self):
        sk = self._setting[self._session_key]
        if sk:
            return sk

        while True:
            login = self._setting[self._login]
            password = self._setting[self._password]

            if login and password:
                sk = self._auth(login, password)
                if sk:
                    self._setting[self._session_key] = sk
                    return sk

                self._setting[self._login] = ''
                self._setting[self._password] = ''

            while True:
                login = xbmcup.gui.prompt(u'Last.fm username')
                if login is None:
                    return None
                if login:
                    break

            while True:
                password = xbmcup.gui.password(u'Last.fm password')
                if password is None:
                    return None
                if password:
                    break

            self._setting[self._login] = login
            self._setting[self._password] = password



    def _auth(self, login, password):
        res = self._api('post', None, **dict(method='auth.getMobileSession', api_key=self._api_key, username=login, password=password))
        if not res:
            return None
        return ET.fromstring(res).findtext('./session/key') or None

        
    def _sig(self, params):
        keys = params.keys()
        keys.sort()
        line = ''
        for key in keys:
            line += str(key)
            line += params[key].encode('utf8') if isinstance(params[key], unicode) else str(params[key])
        line += self._secret_key
        return hashlib.md5(line).hexdigest()
