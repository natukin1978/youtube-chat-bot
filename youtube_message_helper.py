import datetime

from one_comme_users import OneCommeUsers


def create_message_json(item=None) -> dict[str, any]:
    localtime = datetime.datetime.now()
    localtime_iso_8601 = localtime.isoformat()
    json_data = {
        "dateTime": localtime_iso_8601,
        "id": None,
        "displayName": None,
        "nickname": None,
        "content": None,
        "isFirst": False,
        "isFirstOnStream": None,  # すぐ下で設定する
        "noisy": False,
        "additionalRequests": None,
    }
    if item:
        snippet = item["snippet"]
        author = item["authorDetails"]
        json_data["id"] = author["displayName"]
        json_data["displayName"] = author["displayName"]
        json_data["content"] = snippet["displayMessage"]
    OneCommeUsers.update_message_json(json_data)
    return json_data
