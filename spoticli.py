import cmd
import dbus
from dbus.mainloop.glib import DBusGMainLoop

class spoticli(cmd.Cmd):
    intro = 'spoticli, a simple cli for spotify'
    prompt = 'spoticli> '
    ruler = ''
    doc_header = 'commands: '
    undoc_header = ''

    def __init__(self):
        super().__init__()
        bus = dbus.SessionBus(mainloop=DBusGMainLoop(set_as_default=True))
        proxy = bus.get_object('org.mpris.MediaPlayer2.spotify', '/org/mpris/MediaPlayer2')
        self.spotify = dbus.Interface(proxy, dbus_interface='org.mpris.MediaPlayer2.Player')
        self.spotify_properties = dbus.Interface(proxy, 'org.freedesktop.DBus.Properties')

    def on_song_change(self, interface_name, changed_properties, invalid_properties):
        self.do_current()

    def default(self, line):
        print('unrecognized command')

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

    def do_prev(self, line):
        """prev
        play previous song"""
        self.spotify.Previous()

    def do_current(self, line):
        """current
        display info about the current song"""
        metadata = self.spotify_properties.Get('org.mpris.MediaPlayer2.Player', 'Metadata')
        # for key, value in metadata.items():
            # print('Key: {}; Value: {}'.format(key, value))
        song = metadata['xesam:title']
        artist = metadata['xesam:artist'][0]
        album = metadata['xesam:album']
        print('Song:   {}\nArtist: {}\nAlbum:  {}'.format(song, artist, album))

    def do_exit(self, line):
        """exit
        exit the program"""
        return True

if __name__ == '__main__':
    spoticli().cmdloop()
