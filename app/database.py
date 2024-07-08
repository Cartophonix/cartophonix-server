from pocketbase import PocketBase
from config.config import POCKETBASE_URL, POCKETBASE_PORT

# Ensure the URL includes the protocol
client = PocketBase(f"http://{POCKETBASE_URL}:{POCKETBASE_PORT}")

def register_card(uid, playlist, name, image):
    data = {
        "uid": uid,
        "playlist": playlist,
        "name": name,
        "image": image
    }
    client.collection("cards").create(data)

def get_card_by_uid(uid):
    response = client.collection("cards").get_list(1, 1, {"filter": f'uid="{uid}"'})
    if response.items:
        return response.items[0].playlist
    return None

def update_playlist(card_id, new_playlist, new_name, new_image):
    data = {
        "playlist": new_playlist,
        "name": new_name,
        "image": new_image
    }
    client.collection("cards").update(card_id, data)

def delete_card(card_id):
    client.collection("cards").delete(card_id)

def create_alarm(hour, playlist):
    data = {
        "hour": hour,
        "playlist": playlist,
        "activated": True
    }
    client.collection("alarms").create(data)

def list_alarms():
    response = client.collection("alarms").get_list(1, 300)  # Adjust as necessary
    return [{"id": item.id, "hour": item.hour, "playlist": item.playlist, "activated": item.activated} for item in response.items]

def toggle_alarm(alarm_id):
    alarm = client.collection("alarms").get_one(alarm_id)
    new_state = not alarm.activated
    client.collection("alarms").update(alarm_id, {"activated": new_state})

def edit_alarm(alarm_id, new_hour, new_playlist):
    data = {
        "hour": new_hour,
        "playlist": new_playlist
    }
    client.collection("alarms").update(alarm_id, data)

def get_activated_alarms():
    response = client.collection("alarms").get_list(1, 300, {"filter": "activated=True"})  # Adjust as necessary
    return [{"id": item.id, "hour": item.hour, "playlist": item.playlist} for item in response.items]