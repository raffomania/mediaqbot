# MediaQBot
A Telegram bot that enables you to add videos to a queue from any given chat.

## Setup
Install dependencies using `pipenv install`.

### Client
The client makes use of mpv to play all files in the queue, you need a working mpv installation.
Make sure you have pulled all submodules: `git submodule update --init`.

### Server
The server makes use of the Telegram bot API to get newly added videos and servers them to the client via HTTP.
To run the server you will need a running redis instance.
The following environment variables should be set:

* `TELEGRAM_TOKEN` with your Telegram API key
* `REDIS_URL` with the redis connection URL
* `MEDIAQ_PEPPER` a secret used for generating room names to make them less guessable

## TODOs
* More words for more rooms
* Some sensitization of URLs currently we are possibly vulnerable to remote code execution attacks on mpv.
