import json
import asyncio
import requests
from app.database import register_card, get_card_by_uid, update_playlist, get_all_cards
from config.config import MUSIC_HOST, MUSIC_PORT

async def handle_read(websocket, rfid_reader):
    async def read_rfid():
        while True:
            success, uid = rfid_reader.read_uid()
            if success:
                playlist = get_card_by_uid(uid)
                if playlist:
                    response = requests.post(
                        f"http://{MUSIC_HOST}:{MUSIC_PORT}/api/queue/items/add",
                        params={
                            'uris': playlist.playlist,
                            'playback': 'start',
                            'clear': 'true'
                        }
                    )
                    if response.status_code == 200:
                        ws_response = {"status": "success", "uid": uid, "playlist": playlist.playlist}
                    else:
                        ws_response = {"status": "error", "message": "Failed to launch playlist", "uid": uid}
                    await websocket.send(json.dumps(ws_response))
                    print(f"Sent to WebSocket: {json.dumps(ws_response)}")
                else:
                    response = {"status": "error", "message": "Unknown card", "uid": uid}
                    await websocket.send(json.dumps(response))
                    print(f"Sent to WebSocket: {json.dumps(response)}")
                # Wait for the card to be removed before continuing
                card_detected = True
                while rfid_reader.read_uid() == (True, uid):
                    if card_detected:
                        print("Card still detected, waiting for removal...")
                        card_detected = False
                    await asyncio.sleep(0.1)
                # Inform the WebSocket that read mode is active
                read_mode_response = {"status": "info", "message": "Read mode active"}
                await websocket.send(json.dumps(read_mode_response))
                print(f"Sent to WebSocket: {json.dumps(read_mode_response)}")
            await asyncio.sleep(0.1)

    read_task = asyncio.create_task(read_rfid())
    return read_task

async def handle_client(websocket, path, rfid_reader):
    print("Client connected")
    read_task = await handle_read(websocket, rfid_reader)

    # Inform the client about the current mode
    initial_mode_response = {"status": "info", "message": "Read mode active"}
    await websocket.send(json.dumps(initial_mode_response))
    print(f"Sent to WebSocket: {json.dumps(initial_mode_response)}")

    try:
        async for message in websocket:
            print(f"Received message: {message}")
            data = json.loads(message)
            action = data.get("action")

            if action == "register":
                read_task.cancel()  # Pause the read task
                playlist = data.get("playlist")
                print(f"Registering with playlist: {playlist}")
                try:
                    start_time = asyncio.get_event_loop().time()
                    uid = None
                    while asyncio.get_event_loop().time() - start_time < 60:
                        success, uid = await asyncio.to_thread(rfid_reader.read_uid)
                        if success:
                            break
                        await asyncio.sleep(0.1)
                    if not success:
                        raise asyncio.TimeoutError

                    print(f"Scanned UID: {uid}")
                    existing_card = get_card_by_uid(uid)

                    if existing_card:
                        print(f"Updating existing card with UID: {uid}")
                        update_playlist(existing_card.id, playlist)
                        response = {"status": "success", "message": "Card updated", "uid": uid, "playlist": playlist}
                    else:
                        print(f"Registering new card with UID: {uid}")
                        register_card(uid, playlist)
                        response = {"status": "success", "message": "Card registered", "uid": uid, "playlist": playlist}

                    await websocket.send(json.dumps(response))
                    print(f"Sent to WebSocket: {json.dumps(response)}")

                    # Wait for the card to be removed before resuming read task
                    card_detected = True
                    while rfid_reader.read_uid() == (True, uid):
                        if card_detected:
                            print("Card still detected, waiting for removal...")
                            card_detected = False
                        await asyncio.sleep(0.1)

                    print("Card removed, resuming read task")
                    read_task = await handle_read(websocket, rfid_reader)  # Resume the read task

                except asyncio.TimeoutError:
                    response = {"status": "error", "message": "No card detected within timeout"}
                    await websocket.send(json.dumps(response))
                    print(f"Sent to WebSocket: {json.dumps(response)}")
                    print("Timeout: No card detected")

            elif action == "edit":
                cards = get_all_cards()
                response = {"status": "success", "cards": cards}
                await websocket.send(json.dumps(response))
                print(f"Sent to WebSocket: {json.dumps(response)}")
            elif action == "stop_read":
                read_task.cancel()
                break
    except asyncio.CancelledError:
        pass
    except Exception as e:
        response = {"status": "error", "message": str(e)}
        await websocket.send(json.dumps(response))
        print(f"Sent to WebSocket: {json.dumps(response)}")
        print(f"Exception occurred: {e}")