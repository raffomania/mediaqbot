import mpv
import requests
import time
from collections import OrderedDict
import threading
from queue import Queue
import argparse
from subprocess import check_output, CalledProcessError
import json
import logging

logging.getLogger("mediaqclient")
RELOAD_INTERVAL = 1
_server_pop_queue = Queue()


class Playlist:

    def __init__(self):
        self.played = set()
        self.playlist = OrderedDict()

    def update(self, url):
        def dequeue(url, id):
            logging.warn(
                "Can't find a video at %s, setting it to played."
                % url
            )
            _server_pop_queue.put(id)

        try:
            res = requests.get(url)
            logging.debug("Updating playlist from server")
            new_items = []
            for vid in res.json():
                if vid["id"] not in self.playlist.keys():
                    try:
                        url = get_correct_url(vid["url"])
                        if url:
                            new_items.append(
                                (vid["id"], url)
                            )
                        else:
                            dequeue(vid["url"], vid["id"])
                    except ValueError:
                        dequeue(vid["url"], vid["id"])
            if len(new_items) > 0:
                print("Adding new video(s) from server.")
            self.playlist.update(new_items)
        except requests.exceptions.RequestException:
            print("Can't connect to server :(")
            return

    def set_one_played(self, name=None):
        """Registers one video as successfully played."""
        for id, url in self.playlist.items():
            if id not in self.played:
                if name == url.strip():
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
        logging.debug(player.playlist)
        while True:
            tbp_mpv = to_be_played(player)
            tbp_list = len(self.playlist) - len(self.played)
            playlist_count = len(player.playlist)
            playlist_current = player.playlist_pos
            logging.debug("%d, %d" % (tbp_mpv, tbp_list))
            if playlist_current is None and playlist_count > 0:
                logging.debug(
                    "Playlist state 'none' reached. Trying to recover..."
                )
                self.set_mpv_playlist(player)
            if tbp_mpv >= tbp_list:
                break
            index = tbp_mpv
            url = self.not_played[index][1]
            try:
                percent = int(player._get_property("percent-pos"))
            except TypeError:
                percent = 0
            if playlist_count == 0:
                logging.debug("Playing %s now..." % url)
                player.loadfile(url, "replace")
            elif playlist_current is None or \
                    (playlist_count == playlist_current + 1 and percent >= 99):
                logging.debug("Appending and playing %s now..." % url)
                player.loadfile(url, "append")
                player.pause = False
            else:
                logging.debug("Appending %s to mpv playlist" % url)
                player.loadfile(url, mode="append")


def launch():
    parser = argparse.ArgumentParser(
        description="Client for mediaqbot."
    )
    parser.add_argument(
        "playlist_id",
        help="The identifier of your playlist."
    )
    parser.add_argument(
        "hostname",
        help="URL of the mediaqbot server.",
        default="https://mediaq.beep.center",
        nargs="?"
    )
    parser.add_argument(
        "--fullscreen",
        help="Launch mpv in full screen mode.",
        action="store_true"
    )
    parser.add_argument(
        "--reload-interval",
        help="""Set at which interval (in seconds) the
 server is checked for new Items.""",
        dest="interval",
        default=5
    )
    parser.add_argument(
        "--log-level",
        help="One of: CRITICAL, ERROR, WARNING, INFO, DEBUG \
        indicates which error messages should be shown.",
        default=None,
        dest="log_level"
    )
    global RELOAD_INTERVAL
    args = parser.parse_args()
    if args.log_level:
        logging.basicConfig(level=args.log_level)
    RELOAD_INTERVAL = args.interval
    main(args.playlist_id, args.hostname, fullscreen=args.fullscreen)


def main(id, url="https://mediaq.beep.center", fullscreen=False):
    print("Welcome to the mediaqbot client, \
playback will start once a URL is enqueued.")
    full_url = "%s/%s" % (url, id)
    player = mpv.MPV(
        "osc",
        fullscreen=fullscreen,
        ytdl=True,
        input_default_bindings=True,
        input_vo_keyboard=True, video_osd="yes",
        keep_open="yes",
        idle="yes",
        log_file="lol.log"
    )
    playlist = Playlist()
    player.observe_property(
        "percent-pos",
        lambda _, p: check_finished(p if p else 0, player, playlist)
    )
    player.observe_property(
        "playlist-pos",
        lambda _, p: check_track_skip(p, player, playlist)
    )
    pop_thread = threading.Thread(
        target=pop_server,
        args=(_server_pop_queue, full_url),
        daemon=True
    )

    pop_thread.start()
    while True:
        playlist.update(full_url)
        playlist.update_mpv(player)
        time.sleep(RELOAD_INTERVAL)
    # player.wait_for_playback()


def to_be_played(player):
    pos = player.playlist_pos or 0
    length = len(player.playlist)
    try:
        percent = int(player._get_property("percent-pos"))
    except TypeError:
        percent = 0
    if percent >= 99:
        pos += 1
    return length - pos


def check_track_skip(pos, player, playlist):
    # we don't want to remove at launch when on track 0
    if pos and pos > 0:
        old_pos = pos - 1
        name = player.playlist_filenames[old_pos]
        playlist.set_one_played(name)


def pop_server(queue, url):
    while True:
        id = queue.get()
        try:
            r = requests.post(url + "/pop", json={"id": id})
            if r.status_code != 200:
                logging.error("HTTP error %d" % r.status_code)
            else:
                logging.info("Setting %s to 'played'" % id)
        except requests.RequestException as e:
            queue.put(id)
            time.sleep(RELOAD_INTERVAL)
        queue.task_done()


def get_correct_url(url):
    j = None
    try:
        j = check_output(
            ["youtube-dl", "-j", "--skip-download",
             "--max-downloads", "1", url]
        )
        # TODO: handle lists
    except CalledProcessError as e:
        if e.returncode == 101:
            logging.warn(
                "This appears to be a playlist, only playing the first item."
            )
            j = e.output
        elif e.returncode:
            logging.warn("Youtube-dl error :( will skip this item.")
            return None
        else:
            raise
    if j is None:
        return None
    first, _ = j.decode("utf-8").split("\n", 1)
    out = json.loads(first)
    return out["webpage_url"]


def check_finished(percent, player, playlist):
    pos = player.playlist_pos
    if pos is None:
        return None
    name = player.playlist_filenames[pos]
    if percent > 95:
        playlist.set_one_played(name)


launch()
