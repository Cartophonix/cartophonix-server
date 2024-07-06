import base64
import os
from pocketbase import PocketBase
from config.config import POCKETBASE_URL

client = PocketBase(POCKETBASE_URL)

def save_temp_image(base64_data, filename):
    image_data = base64.b64decode(base64_data)
    temp_path = f"/tmp/{filename}"
    with open(temp_path, "wb") as f:
        f.write(image_data)
    return temp_path

def register_card(uid, playlist, name, image=None):
    data = {
        "uid": uid,
        "playlist": playlist,
        "name": name
    }
    files = None
    if image:
        temp_image_path = save_temp_image(image, "card_image.jpg")
        files = {"image": open(temp_image_path, "rb")}
    try:
        if files:
            client.collection("cards").create(data, files=files)
        else:
            client.collection("cards").create(data)
    finally:
        if files:
            files["image"].close()
            os.remove(temp_image_path)

def update_card(card_id, playlist, name=None, image=None):
    data = {
        "playlist": playlist
    }
    if name is not None:
        data["name"] = name
    files = None
    if image is not None:
        temp_image_path = save_temp_image(image, "card_image.jpg")
        files = {"image": open(temp_image_path, "rb")}
    try:
        if files:
            client.collection("cards").update(card_id, data, files=files)
        else:
            client.collection("cards").update(card_id, data)
    finally:
        if files:
            files["image"].close()
            os.remove(temp_image_path)

def get_card_by_uid(uid):
    response = client.collection("cards").get_list(1, 1, {"filter": f'uid="{uid}"'})
    if response.items:
        return response.items[0]
    return None

def update_playlist(card_id, new_playlist):
    data = {
        "playlist": new_playlist
    }
    client.collection("cards").update(card_id, data)

def get_all_cards():
    response = client.collection("cards").get_list(1, 300)  # Adjust as necessary
    return [{"id": item.id, "uid": item.uid, "playlist": item.playlist} for item in response.items]

def delete_card(card_id):
    client.collection("cards").delete(card_id)

# Alarms related functions

def create_alarm(hour, playlist):
    data = {
        "hour": hour,
        "activated": True,
        "playlist": playlist
    }
    client.collection("alarms").create(data)

def list_alarms():
    response = client.collection("alarms").get_list(1, 300)  # Adjust as necessary
    return [{"id": item.id, "hour": item.hour, "activated": item.activated, "playlist": item.playlist} for item in response.items]

def toggle_alarm(alarm_id):
    alarm = client.collection("alarms").get_one(alarm_id)
    new_status = not alarm.activated
    data = {
        "activated": new_status
    }
    client.collection("alarms").update(alarm_id, data)
    return new_status

def edit_alarm(alarm_id, new_hour, new_playlist):
    data = {
        "hour": new_hour,
        "playlist": new_playlist
    }
    client.collection("alarms").update(alarm_id, data)

def delete_alarm(alarm_id):
    client.collection("alarms").delete(alarm_id)