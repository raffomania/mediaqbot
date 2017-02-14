import mpv
import requests
import sys
import time
from collections import OrderedDict
import threading
from queue import Queue
import argparse

RELOAD_INTERVAL = 1
_server_pop_queue = Queue()


class Playlist:

    def __init__(self):
        self.played = set()
        self.playlist = OrderedDict()

    def update(self, url):
        try:
            res = requests.get(url)
            print("Updating playlist form server")
            new_items = [(vid["id"], vid["url"]) for vid in res.json()]
            self.playlist.update(new_items)
        except:
            print("Can't connect to server :(")
            return

    def set_one_played(self, name=None):
        """Registers one video as successfully played."""
        for id, url in self.playlist.items():
            if id not in self.played:
                if name == url:
                    _server_pop_queue.put(id)
                    self.played.add(id)
                    return

    @property
    def not_played(self):
        return [(k, url) for k, url
                in self.playlist.items() if k not in self.played]

    def set_mpv_playlist(self, player):
        player.playlist_clear()
        first = True
        for k, v in self.playlist.items():
            if k not in self.played:
                if first:
                    player.loadfile(v, mode="replace")
                    first = False
                else:
                    player.loadfile(v, mode="append")

    def update_mpv(self, player):
        """Inserts tracks to mpv playlist until the instances total
        length - played tracks is equal the tracks to be played in MPV."""
        while True:
            tbp_mpv = to_be_played(player)
            tbp_list = len(self.playlist) - len(self.played)
            playlist_count = player.playlist_length
            playlist_current = player.playlist_position
            print(tbp_mpv, tbp_list)
            if playlist_current is None and playlist_count > 0:
                print("Playlist state 'none' reached. Trying to recover...")
                self.set_mpv_playlist(player)
            if tbp_mpv >= tbp_list:
                break
            index = tbp_mpv
            url = self.not_played[index][1]
            percent = player._get_property("percent-pos", proptype=int) or 0
            if playlist_count == 0:
                print("Playing %s now..." % url)
                player.loadfile(url, "replace")
            elif playlist_current is None or \
                    (playlist_count == playlist_current + 1 and percent >= 99):
                print("Appending and playing %s now..." % url)
                player.loadfile(url, "append")
                player._set_property("pause", False, proptype=bool)
            else:
                print("Appending %s to mpv playlist" % url)
                player.loadfile(url, mode="append")


def main(id, hostname="mediaq.beep.center"):
    url = "http://" + hostname
    full_url = "%s/%s" % (url, id)
    player = mpv.MPV(
        "osc",
        ytdl=True,
        input_default_bindings=True,
        input_vo_keyboard=True,
        video_osd="yes",
        keep_open="yes",
        idle="yes",
        log_file="lol.log"
    )
    playlist = Playlist()
    player.observe_property(
        "percent-pos",
        lambda p: check_finished(p if p else 0, player, playlist)
    )
    player.observe_property(
        "playlist-pos",
        lambda p: check_track_skip(p, player, playlist)
    )
    pop_thread = threading.Thread(target=pop_server, args=(_server_pop_queue, full_url))
    pop_thread.start()
    while True:
        playlist.update(full_url)
        playlist.update_mpv(player)
        time.sleep(RELOAD_INTERVAL)
    player.wait_for_playback()


def to_be_played(player):
    pos = player.playlist_position or 0
    length = player.playlist_length
    percent = player._get_property("percent-pos", proptype=int) or 0
    if percent >= 99:
        pos += 1
    return length - pos


def check_track_skip(pos, player, playlist):
    # we don't want to remove at launch when on track 0
    if pos and pos > 0:
        old_pos = pos - 1
        name = player._get_property("playlist/%d/filename" % old_pos)
        playlist.set_one_played(name)


def pop_server(queue, url):
    while True:
        id = queue.get()
        try:
            r = requests.post(url + "/pop", json={"id": id})
            if r.status_code != 200:
                print("HTTP error %d" % r.status_code)
            else:
                print("Setting %s to 'played'" % id)
        except requests.RequestException as e:
            queue.put(id)
            time.sleep(RELOAD_INTERVAL)
        queue.task_done()


def check_finished(percent, player, playlist):
    pos = player._get_property("playlist-pos", proptype=int)
    if pos is None:
        return None
    name = player._get_property("playlist/%d/filename" % pos)
    if percent > 95:
        playlist.set_one_played(name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Client for mediaQbot."
    )
    parser.add_argument(
        "playlist_id",
        help="The identifier of your playlist."
    )
    parser.add_argument(
        "hostname",
        help="Hostname of the mediaQbot server.",
        default="mediaq.beep.center",
        nargs="?"
    )
    parser.add_argument(
        "--reload-interval",
        help="Set at which interval (in seconds) the server is polled for new Items.",
        dest="interval",
        default=5
    )
    args = parser.parse_args()
    RELOAD_INTERVAL = args.interval
    main(args.playlist_id, args.hostname)
