import cmd
import dbus
import requests
import time


class spoticli(cmd.Cmd):
    intro = 'spoticli, a simple cli for spotify'
    prompt = '\u001b[32mspoticli' + '\u001b[0m> '
    ruler = ''
    doc_header = 'commands: '
    undoc_header = ''

    def __init__(self):
        super().__init__()
        self.dest = 'org.mpris.MediaPlayer2.spotify'
        self.path = '/org/mpris/MediaPlayer2'
        self.memb = 'org.mpris.MediaPlayer2.Player'
        self.prop = 'org.freedesktop.DBus.Properties'
        self.spotify_url = 'https://api.spotify.com/v1/search/?type=track&q='
        bus = dbus.SessionBus()
        proxy = bus.get_object(self.dest, self.path)
        self.spotify = dbus.Interface(proxy, self.memb)
        self.spotify_properties = dbus.Interface(proxy, self.prop)

    def default(self, line):
        line = line.replace(' ', '%20')
        print('searching...')
        rsp = requests.get(self.spotify_url + line).json()
        try:
            uri = rsp['tracks']['items'][0]['uri']
            self.spotify.OpenUri(uri)
            self.now_playing()
        except IndexError:
            print('could not find song')

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
