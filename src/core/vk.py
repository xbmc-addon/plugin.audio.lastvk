# -*- coding: utf-8 -*-

import xbmcup.net
import xbmcup.app
import xbmcup.gui
import xbmcup.parser

class VKError(Exception):
    __slots__ = ["error"]
    def __init__(self, error_data):
        self.error = error_data
        Exception.__init__(self, str(self))

    @property
    def code(self):
        return self.error['error_code']

    @property
    def message(self):
        return self.error['error_msg']

    def __str__(self):
        return "Error(code = '%s', message = '%s')" % (self.code, self.message)



class VK(object):
    def __init__(self, app_id, setting_login, setting_passowrd, setting_token):
        self._setting = dict(app_id=app_id, login=setting_login, password=setting_passowrd, token=setting_token)

    
    def api(self, method, **kwargs):
        while True:
            token = self._token()
            if token is None:
                return None

            result = self._api(token, method, **kwargs)
            if result is None:
                xbmcup.app.setting[self._setting['token']] = ''
            else:
                return result


    def _api(self, token, method, **kwargs):
        params = dict(access_token=token, v='5.0')
        params.update(kwargs)

        while True:
            response = xbmcup.net.http.get('https://api.vk.com/method/' + method, params=params)

            if response.status_code < 200 or response.status_code > 299:
                raise VKError(dict(error_code=response.status_code, error_msg='HTTP Error', request_params=params))

            result = response.json()

            if 'error' in result:
                if result['error']['error_code'] == 5:
                    return None
                elif result['error']['error_code'] == 14:
                    captcha = self._captcha(result['error']['captcha_img'])
                    if captcha is None:
                        return None
                    else:
                        params.update(dict(captcha_sid=result['error']['captcha_sid'], captcha_key=captcha))
                else:
                    raise VKError(result['error'])
            else:
                return result['response']


    def _captcha(self, url):
        return xbmcup.gui.captcha(url, 130, 50, title='Enter code')


    def _token(self):
        token = xbmcup.app.setting[self._setting['token']]
        if token:
            return token

        while True:
            login = xbmcup.app.setting[self._setting['login']]
            password = xbmcup.app.setting[self._setting['password']]

            if login and password:
                token = self._auth(login, password)
                if token:
                    xbmcup.app.setting[self._setting['token']] = token
                    return token

                xbmcup.app.setting[self._setting['login']] = ''
                xbmcup.app.setting[self._setting['password']] = ''

            while True:
                login = xbmcup.gui.prompt(u'VK username')
                if login is None:
                    return None
                if login:
                    break

            while True:
                password = xbmcup.gui.password(u'VK password')
                if password is None:
                    return None
                if password:
                    break

            xbmcup.app.setting[self._setting['login']] = login
            xbmcup.app.setting[self._setting['password']] = password


    def _auth(self, login, password):
        params = dict(
            client_id=self._setting['app_id'],
            scope='audio',
            redirect_uri='https://oauth.vk.com/blank.html',
            display='mobile',
            v='5.0',
            response_type='token'
        )

        session = xbmcup.net.http.Session()

        response = session.get('https://oauth.vk.com/authorize', params=params)
        if response.status_code < 200 or response.status_code > 299:
            raise VKError(dict(error_code=response.status_code, error_msg='HTTP Error', request_params=params))

        url, inputs = self._parser_form(response.text)
        if url is None:
            raise VKError(dict(error_code=response.status_code, error_msg='OAuth Error', request_params=params))

        inputs['email'] = login
        inputs['pass'] = password

        response = session.post(url, params=inputs)
        if response.status_code < 200 or response.status_code > 299:
            raise VKError(dict(error_code=response.status_code, error_msg='HTTP Error', request_params=params))

        if response.url.find('/blank.html') != -1:
            return self._parser_token(response.url)

        url, inputs = self._parser_form(response.text)
        if url is None:
            raise VKError(dict(error_code=response.status_code, error_msg='OAuth Error', request_params=params))

        response = session.post(url)
        if response.status_code < 200 or response.status_code > 299:
            raise VKError(dict(error_code=response.status_code, error_msg='HTTP Error', request_params=params))

        if response.url.find('/blank.html') != -1:
            return self._parser_token(response.url)

        return None


    def _parser_form(self, html):
        form = xbmcup.parser.re('<form[^>]+action="([^""]+)"[^>]*>(.+)</form>', html)
        if not form:
            return None, None
        inputs = {}
        for tag in xbmcup.parser.re.all('<input[^>]+>', form[1]):
            name = xbmcup.parser.re('name="([^"]+)"', tag[0])
            if name:
                value = xbmcup.parser.re('value="([^"]+)"', tag[0])
                if value:
                    inputs[name[0]] = value[0]
        return form[0], inputs

    def _parser_token(self, uri):
        access_token = xbmcup.parser.re('access_token=([0-9a-f]+)', uri)
        return access_token[0] if access_token and access_token[0] else None
