from telegram.ext import Updater, CommandHandler, Job
import logging
from os import environ
from collections import defaultdict
from flask import Flask, jsonify
from flask_redis import FlaskRedis
import uuid
import json

app = Flask(__name__)
redis_store = FlaskRedis(app)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

def add(bot, update, args):
    chat_id = update.message.chat_id
    url = args[0] if len(args) > 0 else None
    if url:
        tup = json.dumps({"id": str(uuid.uuid4()), "url": url})
        redis_store.rpush(chat_id, tup)

    logger.info("enqing URL %s for chat [%s]" % (url, chat_id))

def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"' % (update, error))

def decode_videos_entry(videos, single=False):
    lst = [json.loads(v.decode("utf-8")) for v in videos]
    if single:
        try:
            return lst[0]
        except IndexError:
            return {}
    else:
        return lst

@app.route("/<chat_id>/current")
def current_video(chat_id):
    return jsonify(decode_videos_entry(redis_store.lrange(chat_id, 0, 1), single=True))

@app.route("/<chat_id>/next")
def next_video(chat_id):
    return jsonify(decode_videos_entry(redis_store.lrange(chat_id, 1, 2), single=True))

@app.route("/<chat_id>")
def video_list(chat_id):
    videos = decode_videos_entry(redis_store.lrange(chat_id, 0, 10))
    return jsonify(videos)

@app.route("/<chat_id>/pop")
def pop_video(chat_id):
    return jsonify({"popped": redis_store.rpop(chat_id).decode("utf-8")})

def main():
    updater = Updater(environ.get("TELEGRAM_TOKEN"))
    redis_store.flushdb()

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("add", add, pass_args=True))

    dp.add_error_handler(error)

    updater.start_polling()
    app.run()

if __name__ == "__main__":
    main()
