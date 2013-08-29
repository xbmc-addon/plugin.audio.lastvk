# -*- coding: utf-8 -*-

import time
import traceback

import xbmc
import xbmcaddon

import xbmcup.app
import xbmcup.gui
import xbmcup.log

import core.lastfm

xbmcup.log.set_prefix('script.service.lastvk')

LASTFM = core.lastfm.LastFM('2c207878e17c021c6ee060f8f39487f2', '570aa4c51ccb896a4130363ca55ecac2', 'plugin.audio.lastvk', 'lastfm_login', 'lastfm_password', 'lastfm_session_key')


class Player(xbmc.Player):
    data = None
    started = False

    def onPlayBackStarted(self):
        xbmc.sleep(2000) # wait (tags are not available now)
        try:
            self._on_started()
        except:
            xbmcup.log.error(traceback.format_exc())

            
    def onPlayBackStopped(self):
        try:
            self._on_stopped()
        except:
            xbmcup.log.error(traceback.format_exc())

    

    def _on_started(self):
        if self.isPlayingAudio():
            info = self.getMusicInfoTag()

            artist = info.getArtist()
            track = info.getTitle()
            album = info.getAlbum()
            duration = int(self.getTotalTime() or info.getDuration())

            if self.data is None or self.data[0] != artist or self.data[1] != track:
                timeout = int(duration/2)
                if timeout > 250: # > 4:10 min
                    timeout = 250

                self.data = artist, track, album, duration, int(time.time()), (int(time.time()) + timeout)
                self.started = True


    def _on_stopped(self):
        self.data = None
        self.started = False


    def check(self):
        if not self.isPlayingAudio():
            self.data = None

        if self.started:
            self.started = False
            return 'start', self.data[0], self.data[1], self.data[2], self.data[3]

        if self.data and self.data[3] > 30 and int(time.time()) > self.data[5]:
            data = 'scrobble', self.data[0], self.data[1], self.data[2], self.data[3], self.data[4]
            self.data = None
            return data





class Service(xbmcup.app.Service):
    def handle(self):
        try:
            data = PLAYER.check()
        except:
            xbmcup.log.error(traceback.format_exc())
        else:
            if data:
                if data[0] == 'start':
                    try:
                        self.now_playing(data[1], data[2], data[3], data[4])
                    except:
                        xbmcup.log.error(traceback.format_exc())

                else:
                    try:
                        self.scrobble(data[1], data[2], data[3], data[4], data[5])
                    except:
                        xbmcup.log.error(traceback.format_exc())

        return 1

    def now_playing(self, artist, track, album, duration):
        if bool(xbmcaddon.Addon(id='plugin.audio.lastvk').getSetting(id='lastfm_scrobbling') == 'true'):
            LASTFM.track.updateNowPlaying(artist=artist, track=track, album=album, duration=duration)


    def scrobble(self, artist, track, album, duration, timestamp):
        if bool(xbmcaddon.Addon(id='plugin.audio.lastvk').getSetting(id='lastfm_scrobbling') == 'true'):
            LASTFM.track.scrobble(artist=artist, track=track, album=album, timestamp=timestamp, duration=duration)


xbmcup.log.notice('Last.VK service started')
PLAYER = Player()
Service().run()
xbmcup.log.notice('Last.VK service stopped')
