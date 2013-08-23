# -*- coding: utf-8 -*-

import xbmcup.net


class FanartTVError(Exception):
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



class FanartTV(object):
    def __init__(self, api_key):
        self._api_key = api_key

    
    def api(self, method, mbid, type='all', sort=1, limit=2):
        """
            method = artist | album | label
            mbid   - go to http://musicbrainz.org
            type   = all | cdart | artistbackground | albumcover | musiclogo | artistthumbs
            sort   = 1 | 2 | 3
            limit  = 1 | 2
        """
        try:
            response = xbmcup.net.http.get('http://api.fanart.tv/webservice/' + method + '/' + self._api_key + '/' + mbid + '/JSON/' + type + '/' + str(sort) + '/' + str(limit) + '/')
        except xbmcup.net.http.exceptions.RequestException:
            raise LastFMError(dict(error=0, message='RequestException'))
        else:
            if response.status_code < 200 or response.status_code > 299:
                raise LastFMError(dict(error=response.status_code, message='HTTP Error'))

            data = response.json()

            # TODO: This workers with backgounds only
            if data:
                bg = data.values()[0].get('artistbackground', [])
                return bg[0]['url'] if bg else None
