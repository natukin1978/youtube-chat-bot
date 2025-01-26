import asyncio
import json
import logging
import os
import sys

import websockets

import global_value as g

g.app_name = "youtube_chat_bot"

from config_helper import readConfig
from one_comme_users import OneCommeUsers
from text_helper import readText
from websocket_helper import websocket_listen_forever
from youtube_bot import YoutubeBot

g.ADDITIONAL_REQUESTS_PROMPT = readText("prompts/additional_requests_prompt.txt")

g.config = readConfig()

# ロガーの設定
logging.basicConfig(level=logging.INFO)

g.map_is_first_on_stream = {}
g.one_comme_users = OneCommeUsers.read_one_comme_users()
g.set_exclude_id = set(readText("exclude_id.txt").splitlines())
# g.set_needs_response = set()
g.websocket_fuyuka = None


async def main():
    def get_fuyukaApi_baseUrl() -> str:
        conf_fa = g.config["fuyukaApi"]
        if not conf_fa:
            return ""
        return conf_fa["baseUrl"]

    def set_ws_fuyuka(ws) -> None:
        g.websocket_fuyuka = ws

    async def recv_fuyuka_response(message: str) -> None:
        return

    bot = YoutubeBot()

    print("前回の続きですか？(y/n) ", end="")
    is_continue = input() == "y"
    if (
        is_continue
        and OneCommeUsers.load_is_first_on_stream()
        and bot.load_live_video_id()
    ):
        print("挨拶キャッシュを復元しました。")

    live_video_id = bot.get_live_video_id()
    if not live_video_id:
        print("live video id: ", end="")
        live_video_id = input()

    if not live_video_id:
        return

    bot.set_live_video_id(live_video_id)
    await bot.run()
    bot.save_live_video_id()

    fuyukaApi_baseUrl = get_fuyukaApi_baseUrl()
    if fuyukaApi_baseUrl:
        websocket_uri = f"{fuyukaApi_baseUrl}/chat/{g.app_name}"
        asyncio.create_task(
            websocket_listen_forever(websocket_uri, recv_fuyuka_response, set_ws_fuyuka)
        )

    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        pass
    finally:
        pass


if __name__ == "__main__":
    asyncio.run(main())
