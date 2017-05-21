import cmd
import dbus
import requests
import time

class spoticli(cmd.Cmd):
    intro = 'spoticli, a simple cli for spotify'
    prompt = '\033[92mspoticli' + '\033[0m> '
    ruler = ''
    doc_header = 'commands: '
    undoc_header = ''

    def __init__(self):
        super().__init__()
        bus = dbus.SessionBus()
        proxy = bus.get_object('org.mpris.MediaPlayer2.spotify', '/org/mpris/MediaPlayer2')
        self.spotify = dbus.Interface(proxy, dbus_interface='org.mpris.MediaPlayer2.Player')
        self.spotify_properties = dbus.Interface(proxy, 'org.freedesktop.DBus.Properties')

    def default(self, line):
        line = line.replace(' ', '%20')
        print('searching...')
        data = requests.get('https://api.spotify.com/v1/search/?type=track&q=' + line).json()
        uri = data['tracks']['items'][0]['uri']
        self.spotify.OpenUri(uri)
        self.now_playing()

    def get_metadata(self):
        metadata = self.spotify_properties.Get('org.mpris.MediaPlayer2.Player', 'Metadata')
        # for key, value in metadata.items():
            # print('Key: {}; Value: {}'.format(key, value))
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

    def do_current(self, line):
        """current
        display info about the current song"""
        song, artist, album = self.get_metadata()
        print('song:   {}\nartist: {}\nalbum:  {}'.format(song, artist, album))

    def now_playing(self, sleep=True):
        if sleep:
            time.sleep(.1)
        song, artist, album = self.get_metadata()
        song = '\u001b[36m{}\u001b[0m'.format(song)
        artist = '\u001b[34m{}\u001b[0m'.format(artist)
        print('playing {} by {}'.format(song, artist))

    def do_exit(self, line):
        """exit
        exit the program"""
        return True

if __name__ == '__main__':
    spoticli().cmdloop()
