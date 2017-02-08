import mpv

URL = "localhost:8080"
FINISHED = []

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

    playlist = update_playlist()
    if len(playlist) > 0:
        player.play(playlist[0])
        for url in playlist[1:]:
            player.loadfile(url, mode="append")

    # this waiting could be done nicer, maybe wait for exit event?
    while True:
        pass


def update_playlist(existing_list=[]):
    return ["https://www.youtube.com/watch?v=mS-mrt3Dywc", "https://www.youtube.com/watch?v=3eBQUjGD7jw"]


def check_track_skip(pos, player):
    # we don't want to remove at launch when on track 0
    if pos > 0:
        old_pos = pos - 1
        name = player._get_property("playlist/%d/filename" % old_pos)
        set_finished(old_pos, name)


def set_finished(index, name):
    global FINISHED
    if index in FINISHED:
        return
    else:
        # if some server reques succeds:
        print("Should be popping on server")
        FINISHED.append(index)
        # send name to server


def check_finished(percent, player):
    pos = player._get_property("playlist-pos", proptype=int) or 0
    name = player._get_property("playlist/%d/filename" % pos)
    if percent > 95:
        set_finished(pos, name)


if __name__ == "__main__":
    main()
