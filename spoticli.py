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
            print('error in response: ' + response)
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
        search_type = words[0]
        if search_type == 'song':
            search_type = 'track'
        query = ' '.join(words[1:])
        self.search(search_type, query)

    def complete_search(self, text, line, begidx, endidx):
        return [i for i in ('track', 'artist', 'album', 'playlist') if i.startswith(text)]

    def search(self, search_type, query):
        params = {
            'type': search_type,
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
        options = rsp[search_type + 's']['items']
        num = 0
        if search_type == 'track':
            num = self.choose_track(options)
        elif search_type == 'artist':
            num = self.choose_artist(options)
        elif search_type == 'album':
            num = self.choose_album(options)
        elif search_type == 'playlist':
            num = self.choose_playlist(options)
        else:
            print('invalid search type')
        if num < 0:
            return
        try:
            uri = rsp[search_type + 's']['items'][num]['uri']
            self.spotify.OpenUri(uri)
            self.now_playing()
        except IndexError:
            print('could not find ' + search_type + ' with query ' + query)

    def choose_track(self, tracks):
        for idx, track in enumerate(tracks):
            print(str(idx + 1) + '. ' + self.printable_song(track['name'], track['artists'][0]['name'], track['album']['name']))
        return int(input('enter the number for the track you want: ')) - 1

    def choose_artist(self, artists):
        for idx, artist in enumerate(artists):
            print(str(idx + 1) + '. ' + self.printable_artist(artist['name'], artist['genres']))
        return int(input('enter the number for the artist you want: ')) - 1

    def choose_album(self, albums):
        for idx, album in enumerate(albums):
            print(str(idx + 1) + '. ' + self.printable_album(album['name'], album['artists'][0]['name']))
        return int(input('enter the number for the album you want: ')) - 1

    def choose_playlist(self, playlists):
        for idx, playlist in enumerate(playlists):
            print(str(idx + 1) + '. ' + self.printable_playlist(playlist['name'], playlist['owner']['id']))
        return int(input('enter the number of the playlist you want: ')) - 1

    def now_playing(self, sleep=True):
        if sleep:
            time.sleep(.2)
        song, artist, album = self.get_metadata()
        print(self.printable_song(song, artist, album))

    def printable_song(self, song, artist, album):
        song = '\u001b[36m{}\u001b[0m'.format(song)
        artist = '\u001b[34m{}\u001b[0m'.format(artist)
        album = '\u001b[35m{}\u001b[0m'.format(album)
        return '{} by {} on {}'.format(song, artist, album)

    def printable_artist(self, artist, genres):
        artist = '\u001b[36m{}\u001b[0m'.format(artist)
        genre_str = ''
        if genres:
            genre_str = ' genres:'
            for genre in genres:
                genre_str += ' ' + genre + ','
            genre_str = genre_str[:-1]
        return artist + genre_str

    def printable_album(self, album, artist):
        album = '\u001b[36m{}\u001b[0m'.format(album)
        artist = '\u001b[34m{}\u001b[0m'.format(artist)
        return '{} by {}'.format(album, artist)

    def printable_playlist(self, name, owner):
        name = '\u001b[36m{}\u001b[0m'.format(name)
        owner = '\u001b[34m{}\u001b[0m'.format(owner)
        return '{} by {}'.format(name, owner)

    def do_exit(self, line):
        """exit
        exit the program"""
        return True

if __name__ == '__main__':
    spoticli().cmdloop()
