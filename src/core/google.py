# -*- coding: utf-8 -*-

import urllib
import cgi
import json

import xbmcup.net

class ImageSearch:
    def search(self, query, **kwargs):
        if isinstance(query, unicode):
            query = query.encode('utf8')
        kwargs['q'] = urllib.quote(query)
        kwargs['v'] = '1.0'
        
        response = xbmcup.net.http.get('http://ajax.googleapis.com/ajax/services/search/images', params=kwargs)
        if response.status_code != 200:
            return None
        data = response.json()
        
        


class YouTube:
    # https://code.google.com/p/youtubexbmc/source/browse/trunk/YouTubePlayer.py

    quality = [
        
        #(?,  38, ''),      # 720p vp8 webm container

        #(?,  46, ''),      # 520p vp8 webm stereo
        #(?,  82, ''),      # 360p h264 stereo
        #(?,  83, ''),      # 240p h264 stereo
        #(?,  84, ''),      # 720p h264 stereo
        #(?,  85, ''),      # 520p h264 stereo
        #(?, 100, ''),      # 360p vp8 webm stereo
        #(?, 101, ''),      # 480p vp8 webm stereo
        #(?, 102, ''),      # 720p vp8 webm stereo

        
        ( 1,   5, '240p'),  # 240p h263 flv container
        ( 2,  33, ''),      # ???
        ( 3,  18, ''),      # 360p h264 mp4 container | 270 for rtmpe?
        ( 4,  26, ''),      # ???
        ( 5,  43, ''),      # 360p h264 flv container
        ( 6,  34, '360p'),  # 360p h264 flv container
        ( 7,  78, ''),      # seems to be around 400 for rtmpe
        ( 8,  44, ''),      # 480p vp8 webm container
        ( 9,  59, ''),      # 480 for rtmpe
        (10,  35, '480p'),  # 480p h264 flv container
        (11, 120, ''),      # hd720
        (12,  45, ''),      # 720p vp8 webm container
        (13,  22, '720p'),  # 720p h264 mp4 container
        (14, 121, ''),      # hd1080
        (15,  37, '1080p')  # 1080p h264 mp4 container

    ]


    def resolve(self, vid, max_quality=None, stereo=None):
        if max_quality:
            max_quality = [x[0] for x in self.quality if x[2] == max_quality][0]

        response = xbmcup.net.http.get('http://www.youtube.com/watch?v=' + vid + '&safeSearch=none')
        if response.status_code != 200:
            return None

        flashvars = self._flashvars(response.content)
        if not flashvars:
            return None

        links = []

        for raw in flashvars.get('url_encoded_fmt_stream_map', '').split(','):
            try:
                data = cgi.parse_qs(raw)
            except:
                pass
            else:

                if not self._stereo(data, stereo):
                    continue

                quality = self._quality(data, max_quality)
                if not quality:
                    continue

                url = self._url(data)
                if not url:
                    continue

                signature = self._signatue(data)
                if signature is not None:
                    url += signature

                links.append((quality, url))                

        if not links:
            return flashvars.get('hlsvp')

        links.sort(cmp=lambda (q1, t1), (q2, t2): cmp(q1, q2))
        return links[-1][1]


    def _flashvars(self, html):
        for line in html.split('\n'):
            line = line.strip()
            start = line.find(';ytplayer.config = ')
            if start != -1:
                start += 19
                end = line.rfind(';')
                if end != -1:

                    line = line[start:end]

                    # remove additional ending delimiter
                    pos = line.find('};')
                    if pos != -1:
                        line = line[:pos + 1]

                    try:
                        return json.loads(line)['args']
                    except:
                        return None
        return None


    def _stereo(self, data, stereo):
        if stereo is None:
            return True

        if stereo and 'stereo3d' not in data:
            return False
        elif not stereo and 'stereo3d' in data:
            return False
        else:
            return True


    def _quality(self, data, max_quality):
        itag_s = data.get('itag')
        if not itag_s:
            return None

        itag = int(itag_s[0])
        quality = [x[0] for x in self.quality if x[1] == itag]

        if not quality:
            return None

        if max_quality and quality[0] > max_quality:
            return None

        return quality[0]


    def _url(self, data):
        if 'url' in data:
            return urllib.unquote(data['url'][0])

        if 'stream' in data:
            if 'conn' in data:
                url = urllib.unquote(data['conn'][0])
                if not url.endswith('/'):
                    url += '/'
                return url + urllib.unquote(data['stream'][0])
            else:
                return urllib.unquote(data['stream'][0])


    def _signatue(self, data):
        if 'sig' in data:
            return '&signature=' + data['sig'][0]

        if 's' in data:
            decrypt = self._decrypt_signature(data['s'][0])
            return ''.join(['&signature=', decrypt]) if decrypt else None
        
        return ''


    def _decrypt_signature(self, s):
        ''' use decryption solution by Youtube-DL project '''

        w = len(s)

        if w == 92:
            return s[25] + s[3:25] + s[0] + s[26:42] + s[79] + s[43:79] + s[91] + s[80:83]

        if w == 90:
            return s[25] + s[3:25] + s[2] + s[26:40] + s[77] + s[41:77] + s[89] + s[78:81]

        if w == 88:
            return s[48] + s[81:67:-1] + s[82] + s[66:62:-1] + s[85] + s[61:48:-1] + s[67] + s[47:12:-1] + s[3] + s[11:3:-1] + s[2] + s[12]

        if w == 87:
            return s[4:23] + s[86] + s[24:85]

        if w == 86:
            return s[83:85] + s[26] + s[79:46:-1] + s[85] + s[45:36:-1] + s[30] + s[35:30:-1] + s[46] + s[29:26:-1] + s[82] + s[25:1:-1]

        if w == 85:
            return s[2:8] + s[0] + s[9:21] + s[65] + s[22:65] + s[84] + s[66:82] + s[21]

        if w == 84:
            return s[83:36:-1] + s[2] + s[35:26:-1] + s[3] + s[25:3:-1] + s[26]

        if w == 83:
            return s[6] + s[3:6] + s[33] + s[7:24] + s[0] + s[25:33] + s[53] + s[34:53] + s[24] + s[54:]

        if w == 82:
            return s[36] + s[79:67:-1] + s[81] + s[66:40:-1] + s[33] + s[39:36:-1] + s[40] + s[35] + s[0] + s[67] + s[32:0:-1] + s[34]

        if w == 81:
            return s[56] + s[79:56:-1] + s[41] + s[55:41:-1] + s[80] + s[40:34:-1] + s[0] + s[33:29:-1] + s[34] + s[28:9:-1] + s[29] + s[8:0:-1] + s[9]

