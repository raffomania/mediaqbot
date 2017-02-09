import mpv
import requests
import sys
import time
from collections import OrderedDict

URL = "http://localhost:5000"
ID = sys.argv[1]
FULL_URL = "%s/%s" % (URL, ID)
RELOAD_INTERVAL = 1

class Playlist:
    def __init__(self):
        self.played = set()
        self.playlist = OrderedDict()

    def update(self):
        res = requests.get(FULL_URL)
        print("Updating playlist form server")
        new_items = [(vid["id"], vid["url"]) for vid in res.json()]
        self.playlist.update(new_items)

    def set_one_played(self, name=None):
        """Registers one video as successfully played."""
        for id, url in self.playlist.items():
            if id not in self.played:
                if name == url:
                    print("Setting %s to 'played'" % name)
                    # Todo: some queue for to pop items
                    r = requests.get(FULL_URL + "/pop")
                    self.played.add(id)
                return

    @property
    def not_played(self):
        return [(k, url) for k, url in self.playlist.items() if k not in self.played]

    def update_mpv(self, player):
        """Inserts tracks to mpv playlist until the instances total length - played tracks 
        is equal the tracks to be played in MPV."""
        print(self.played)
        while True:
            tbp_mpv = to_be_played(player)
            tbp_list = len(self.playlist) - len(self.played)
            print("mpv playlist still has %d to play while playlist class has %d" % (tbp_mpv, tbp_list))
            if tbp_mpv >= tbp_list:
                break
            index = tbp_mpv
            url = self.not_played[index][1]
            playlist_count = player._get_property("playlist-count", proptype=int)
            if playlist_count == 0:
                print("Playing %s now..." % url)
                player.loadfile(url, "replace")
            else:
                print("Appending %s to mpv playlist" % url)
                player.loadfile(url, mode="append")


def main():
    player = mpv.MPV(
        "osc",
        ytdl=True,
        input_default_bindings=True,
        input_vo_keyboard=True,
        video_osd="yes",
        keep_open="yes",
        log_file="lol.log"
    )
    playlist = Playlist()
    player.observe_property("percent-pos", lambda p: check_finished(p if p else 0, player, playlist))
    player.observe_property("playlist-pos", lambda p: check_track_skip(p, player, playlist))
    while True:
        playlist.update()
        playlist.update_mpv(player)
        time.sleep(RELOAD_INTERVAL)
    player.wait_for_playback()



def to_be_played(player):
    pos = player._get_property("playlist-pos", proptype=int) or 0
    length = player._get_property("playlist-count", proptype=int)
    return length - pos #length - (pos + 1)


def check_track_skip(pos, player, playlist):
    # we don't want to remove at launch when on track 0
    if pos and pos > 0:
        old_pos = pos - 1
        name = player._get_property("playlist/%d/filename" % old_pos)
        playlist.set_one_played(name)


def check_finished(percent, player, playlist):
    pos = player._get_property("playlist-pos", proptype=int) or 0
    name = player._get_property("playlist/%d/filename" % pos)
    if percent > 95:
        playlist.set_one_played(name)


if __name__ == "__main__":
    main()
