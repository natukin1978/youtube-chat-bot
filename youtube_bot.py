import asyncio
import datetime
import logging
import pickle
import os

from googleapiclient.discovery import build

import global_value as g
from cache_helper import get_cache_filepath
from fuyuka_helper import Fuyuka
from one_comme_users import OneCommeUsers
from random_helper import is_hit_by_message_json
from youtube_message_helper import create_message_json_from_youtube_item

logger = logging.getLogger(__name__)


class YoutubeBot:
    FILENAME_LIVE_VIDEO_ID = get_cache_filepath(f"{g.app_name}_live_video_id.pkl")

    def __init__(self):
        self.live_video_id = ""
        self.api_key = g.config["youtube"]["apiKey"]
        self.chat_polling_interval = g.config["youtube"]["chatPollingIntervalSec"]
        self.youtube = build("youtube", "v3", developerKey=self.api_key)
        self.chat_task = None
        self.live_chat_id = None

    def load_live_video_id(self) -> bool:
        if not os.path.isfile(self.FILENAME_LIVE_VIDEO_ID):
            return False
        with open(self.FILENAME_LIVE_VIDEO_ID, "rb") as f:
            self.live_video_id = pickle.load(f)
            return True

    def save_live_video_id(self) -> None:
        with open(self.FILENAME_LIVE_VIDEO_ID, "wb") as f:
            pickle.dump(self.live_video_id, f)

    def get_live_video_id(self) -> str:
        return self.live_video_id

    def set_live_video_id(self, live_video_id: str) -> None:
        self.live_video_id = live_video_id

    async def on_message(self, items):
        for item in items:
            json_data = create_message_json_from_youtube_item(item)

            id = json_data["id"]
            if id in g.set_exclude_id:
                # 無視するID
                return

            answer_level = g.config["fuyukaApi"]["answerLevel"]
            answer_length = g.config["fuyukaApi"]["answerLength"]["default"]
            needs_response = is_hit_by_message_json(answer_level, json_data)
            OneCommeUsers.update_additional_requests(json_data, answer_length)
            await Fuyuka.send_message_by_json_with_buf(json_data, needs_response)

    async def get_live_chat_id(self):
        try:
            videos_request = self.youtube.videos().list(
                part="liveStreamingDetails", id=self.live_video_id
            )
            videos_response = videos_request.execute()

            vr_items = videos_response["items"]
            if not vr_items:
                logger.error("Invalid video ID or not a live stream.")
                return None

            self.live_chat_id = vr_items[0]["liveStreamingDetails"]["activeLiveChatId"]
            return self.live_chat_id
        except Exception as e:
            logger.error(f"Error getting live chat ID: {e}")
            return None

    async def get_chat_messages(self):
        if not self.live_chat_id:
            logger.error("Live chat ID is not set. Please call get_live_chat_id first.")
            return

        next_page_token = None
        try:
            while True:
                param = {
                    "part": "id,snippet,authorDetails",
                    "liveChatId": self.live_chat_id,
                    "key": self.api_key,
                }
                if next_page_token:
                    param["pageToken"] = next_page_token

                request = self.youtube.liveChatMessages().list(**param)
                response = request.execute()
                items = response.get("items", [])
                await self.on_message(items)
                next_page_token = response.get("nextPageToken")
                await asyncio.sleep(self.chat_polling_interval)
        except asyncio.CancelledError:
            logger.error("Chat message task cancelled.")
        except Exception as e:
            logger.error(f"Chat message get error:{e}")

    async def run(self):
        self.live_chat_id = await self.get_live_chat_id()
        if not self.live_chat_id:
            return
        self.chat_task = asyncio.create_task(self.get_chat_messages())
