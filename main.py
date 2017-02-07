from telegram.ext import Updater, CommandHandler, Job
import logging
from os import environ
from subprocess import Popen
from http.server import HTTPServer, BaseHTTPRequestHandler
from collections import defaultdict
import urllib
from queue import Queue

PORT = 8000

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

class Chat:
    def __init__(self, id=None, authorized=False):
        self.queue = Queue()
        self.id = id
        self.authorized = authorized

chats = defaultdict(Chat)

def register(bot, update, args):
    chat_id = update.message.chat_id
    password = args[0] if len(args) > 0 else None

    if password == environ.get("PASSWORD"):
        chats[chat_id] = Chat(chat_id, authorized=True)
        logger.info("authorized chat [%s]" % chat_id)
        update.message.reply_text("Access granted")
    elif password is None:
        update.message.reply_text("Enter a valid password.")
    else:
        text = update.message.text
        logger.info("unauthorized attempt from [%s] (%s)" % (chat_id, text))
        update.message.reply_text("You shall not pass!")

def add(bot, update, args):
    chat = chats[update.message.chat_id]
    url = args[0] if len(args) > 0 else None

    if chat.authorized and url:
        chat.queue.put(url)
        logger.info("enqing URL %s for chat [%s]" % (url, chat.id))
    elif url is None:
        update.message.reply_text("Please provide a URL")
    else:
        update.message.reply_text("I'm sorry Dave, I'm afraid I can't do that.")

def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"' % (update, error))

class HTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        chat_id = int(urllib.parse.urlparse(self.path).path[1:])
        chat = chats[chat_id]
        if chat.authorized:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(chats[chat_id].queue.queue[0].encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()
            logger.info("404 [%s]" % chat_id)
            self.wfile.write("lel no du wichser".encode("utf-8"))


def http_listen(server_class=HTTPServer, handler_class=HTTPHandler):
    server_address = ('', 8000)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

def main():
    updater = Updater(environ.get("TELEGRAM_TOKEN"))

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("register", register, pass_args=True))
    dp.add_handler(CommandHandler("add", add, pass_args=True))

    dp.add_error_handler(error)

    updater.start_polling()
    http_listen()

if __name__ == "__main__":
    main()
