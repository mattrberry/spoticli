#!/usr/bin/env python3

import cmd
import dbus
import requests
import time
import json
from base64 import b64encode
from os import environ


class spoticli(cmd.Cmd):
    intro = 'spoticli, a simple cli for spotify'
    prompt = '\u001b[32m' + 'spoticli' + '\u001b[0m> '
    ruler = ''
    doc_header = 'commands: '
    undoc_header = ''

    def __init__(self):
        super().__init__()
        self.dest = 'org.mpris.MediaPlayer2.spotify'
        self.path = '/org/mpris/MediaPlayer2'
        self.memb = 'org.mpris.MediaPlayer2.Player'
        self.prop = 'org.freedesktop.DBus.Properties'
        self.spotify_url = 'https://api.spotify.com/v1/search/'
        bus = dbus.SessionBus()
        try:
            proxy = bus.get_object(self.dest, self.path)
            self.spotify = dbus.Interface(proxy, self.memb)
            self.spotify_properties = dbus.Interface(proxy, self.prop)
        except:
            print('spotify needs to be running')
            exit()

        self.headers = {'Authorization': 'Basic ' + b64encode(environ['spotify_creds'].encode('utf-8')).decode('utf-8')}
        self.data = {'grant_type': 'client_credentials'}
        self.new_auth()
        print(self.auth_token)

    def cmdloop(self, intro=None):
        print(self.intro)
        while True:
            try:
                super(spoticli, self).cmdloop(intro='')
                self.postloop()
                break
            except KeyboardInterrupt:
                print('^C')

    def new_auth(self):
        auth_response = requests.post('https://accounts.spotify.com/api/token', headers=self.headers, data=self.data)
        self.auth_token = json.loads(auth_response.text)['access_token']
        self.headers = {
            'Authorization': 'Bearer ' + self.auth_token
        }
        

    def check_good_auth(self, response):
        if 'error' in response:
            self.new_auth()
            return False
        return True

    def default(self, line):
        print('\u001b[31m' + 'invalid command. use "help" or "?" to see instructions' + '\u001b[0m')

    def get_metadata(self):
        metadata = self.spotify_properties.Get(self.memb, 'Metadata')
        song = metadata['xesam:title']
        artist = metadata['xesam:artist'][0]
        album = metadata['xesam:album']
        return (song, artist, album)

    def precmd(self, line):
        if line == 'EOF':
            return 'exit'
        return line

    def do_play(self, line):
        """play
        play current song"""
        self.spotify.Play()

    def do_pause(self, line):
        """pause
        pause current song"""
        self.spotify.Pause()

    def do_pp(self, line):
        """pp
        play/pause current song"""
        self.spotify.PlayPause()

    def do_next(self, line):
        """next
        skip this song"""
        self.spotify.Next()
        self.now_playing()

    def do_prev(self, line):
        """prev
        play previous song"""
        self.spotify.Previous()
        self.now_playing()

    def do_song(self, line):
        """song
        display info about the current song"""
        self.now_playing(False)

    def do_search(self, line):
        """search
        search for a track, artist, album, or playlist
        type 'search' followed by one of those 
        terms and your search query"""
        words = line.split()
        t = words[0]
        query = ' '.join(words[1:])
        self.search(t, query)

    def search(self, t, query):
        params = {
            'type': t,
            'q': query
        }
        print('searching...')
        while True:
            rsp = requests.get(self.spotify_url, params=params, headers=self.headers).json()
            if self.check_good_auth(rsp):
                break
            else:
                print(rsp)
        # print(json.dumps(rsp, indent=4, sort_keys=True))
        try:
            options = rsp[t + 's']['items']
            uri = rsp[t + 's']['items'][0]['uri']
            self.spotify.OpenUri(uri)
            self.now_playing()
        except IndexError:
            print('could not find ' + t + ' with query ' + query)


    def now_playing(self, sleep=True):
        if sleep:
            time.sleep(.2)
        song, artist, album = self.get_metadata()
        song = '\u001b[36m{}\u001b[0m'.format(song)
        artist = '\u001b[34m{}\u001b[0m'.format(artist)
        album = '\u001b[35m{}\u001b[0m'.format(album)
        print('{} by {} on {}'.format(song, artist, album))

    def do_exit(self, line):
        """exit
        exit the program"""
        return True

if __name__ == '__main__':
    spoticli().cmdloop()
