import mpv
import requests
import sys
import time

URL = "http://localhost:5000"
ID = sys.argv[1]
QUERY = "%s/%s" % (URL, ID)
FINISHED = []
RELOAD_INTERVAL = 5

def main():
    player = mpv.MPV(
        "osc",
        ytdl=True,
        input_default_bindings=True,
        input_vo_keyboard=True,
        video_osd="yes",
        keep_open="yes"
    )
    player.observe_property("percent-pos", lambda p: check_finished(p if p else 0, player))
    player.observe_property("playlist-pos", lambda p: check_track_skip(p, player))
    playlist = []
    while True:
        playlist = get_playlist()
        if len(playlist) == 0:
            time.sleep(RELOAD_INTERVAL)
        else:
            break
    player.play(playlist[0]["url"])

    # this waiting could be done nicer, maybe wait for exit event?
    while True:
        print(playlist)
        playlist = update_playlist(playlist, player)
        time.sleep(RELOAD_INTERVAL)


def get_playlist():
    current = get_current()
    return [current] if current != {} else []


def update_playlist(existing, player):
    next = get_next()
    if len(existing) == 0:
        return get_playlist()
    if next != {} and next["id"] != existing[-1]["id"]:
        player.loadfile(next["url"], mode="append")
        existing.append(next)
    return existing


def get_next():
    r = requests.get(QUERY + "/next")
    return r.json()


def get_current():
    r = requests.get(QUERY + "/current")
    return r.json()


def check_track_skip(pos, player):
    # we don't want to remove at launch when on track 0
    if pos and pos > 0:
        old_pos = pos - 1
        name = player._get_property("playlist/%d/filename" % old_pos)
        set_finished(old_pos, name)


def set_finished(index, name):
    global FINISHED
    if index in FINISHED:
        return
    else:
        r = requests.get(QUERY + "/pop")
        if r.status_code == 200:
            print("Popped from server queue")
            FINISHED.append(index)
        # send name to server


def check_finished(percent, player):
    pos = player._get_property("playlist-pos", proptype=int) or 0
    name = player._get_property("playlist/%d/filename" % pos)
    if percent > 95:
        set_finished(pos, name)


if __name__ == "__main__":
    main()
