"""Dashboard API - FastAPI endpoints for bot management."""

import asyncio
import os
import time
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from main.config import DOWNLOAD_DIR, TARGET_CHANNEL

app = FastAPI(title="Melos Dashboard", version="1.0.0")

# Will be injected by run.py when the bot starts
_bot = None
_admin_handler = None
_playlist_manager = None
_analytics = None


def init_dashboard(bot, admin_handler, playlist_manager, analytics):
    """Inject bot services into the dashboard API.

    Call this after all services are created in run.py.
    """
    global _bot, _admin_handler, _playlist_manager, _analytics
    _bot = bot
    _admin_handler = admin_handler
    _playlist_manager = playlist_manager
    _analytics = analytics


# ─── Static files ───

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")),
    name="static",
)


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the dashboard frontend."""
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    with open(os.path.join(static_dir, "index.html"), "r", encoding="utf-8") as f:
        return f.read()


# ─── Bot Status ───

@app.get("/api/status")
async def get_status():
    """Get bot status and connection info."""
    if _bot is None:
        raise HTTPException(status_code=503, detail="Bot not initialized")

    is_playing = _bot.audio_player.is_playing() if hasattr(_bot, "audio_player") else False
    is_paused = _bot.audio_player.is_paused() if hasattr(_bot, "audio_player") else False
    queue_size = _bot.request_queue.qsize() if hasattr(_bot, "request_queue") else 0
    uptime = time.time() - _bot._start_time if hasattr(_bot, "_start_time") else 0

    repeat_info = {"mode": "off", "count": 0, "remaining": 0}
    if hasattr(_bot, "repeat_mode"):
        repeat_info = {
            "mode": _bot.repeat_mode,
            "count": getattr(_bot, "repeat_count", 0),
            "remaining": getattr(_bot, "repeat_remaining", 0),
        }

    return {
        "running": _bot._running,
        "is_playing": is_playing,
        "is_paused": is_paused,
        "queue_size": queue_size,
        "uptime_seconds": uptime,
        "repeat": repeat_info,
        "connected": hasattr(_bot, "twitch_handler") and _bot.twitch_handler.is_connected(),
    }


# ─── Queue ───

@app.get("/api/queue")
async def get_queue(limit: int = Query(50, ge=1, le=500)):
    """Get current queue items."""
    if _bot is None:
        raise HTTPException(status_code=503, detail="Bot not initialized")

    items = await _bot.request_queue.get_all_items()
    result = []
    for i, item in enumerate(items[:limit]):
        result.append({
            "position": i + 1,
            "request_id": item.request_id,
            "query": item.query,
            "username": item.username,
            "channel_id": item.channel_id,
            "added_at": getattr(item, "added_at", None),
            "resolved_title": getattr(item, "resolved_title", None),
            "resolved_duration": getattr(item, "resolved_duration", None),
        })
    return {"items": result, "total": len(items)}


@app.delete("/api/queue/{position}")
async def remove_from_queue(position: int):
    """Remove a song from the queue by position (1-based)."""
    if _bot is None:
        raise HTTPException(status_code=503, detail="Bot not initialized")

    removed = await _bot.request_queue.remove_by_index(position - 1)
    if removed is None:
        raise HTTPException(status_code=404, detail=f"No song at position {position}")

    await _bot._persist_queue()
    msg = f"🗑️ Removed '{removed.query}' from queue via dashboard"
    await _bot.chat_message.send_public(TARGET_CHANNEL, msg)
    return {"removed": {"query": removed.query, "username": removed.username}}


@app.delete("/api/queue")
async def clear_queue():
    """Clear the entire queue."""
    if _bot is None:
        raise HTTPException(status_code=503, detail="Bot not initialized")

    await _bot.request_queue.clear()
    await _bot._persist_queue()
    await _bot.chat_message.send_public(TARGET_CHANNEL, "🗑️ Queue cleared via dashboard")
    return {"message": "Queue cleared"}


@app.post("/api/playback/skip")
async def skip_current():
    """Skip the currently playing song."""
    if _bot is None:
        raise HTTPException(status_code=503, detail="Bot not initialized")

    success = _bot.skip_current_song()
    if not success:
        raise HTTPException(status_code=400, detail="No song currently playing")

    await _bot.chat_message.send_public(TARGET_CHANNEL, "⏭ Song skipped via dashboard")
    return {"message": "Song skipped"}


# ─── Playback Controls ───

@app.post("/api/playback/pause")
async def pause_playback():
    """Pause the current song."""
    if _bot is None:
        raise HTTPException(status_code=503, detail="Bot not initialized")

    _bot.audio_player.pause()
    await _bot.chat_message.send_public(TARGET_CHANNEL, "⏸ Playback paused via dashboard")
    return {"message": "Playback paused"}


@app.post("/api/playback/resume")
async def resume_playback():
    """Resume the current song."""
    if _bot is None:
        raise HTTPException(status_code=503, detail="Bot not initialized")

    _bot.audio_player.resume()
    await _bot.chat_message.send_public(TARGET_CHANNEL, "▶ Playback resumed via dashboard")
    return {"message": "Playback resumed"}


@app.post("/api/playback/stop")
async def stop_playback():
    """Stop the current song."""
    if _bot is None:
        raise HTTPException(status_code=503, detail="Bot not initialized")

    _bot.audio_player.stop()
    await _bot.chat_message.send_public(TARGET_CHANNEL, "⏹ Playback stopped via dashboard")
    return {"message": "Playback stopped"}


@app.post("/api/playback/volume")
async def set_volume(level: int = Query(..., ge=0, le=100)):
    """Set volume level (0-100)."""
    if _bot is None:
        raise HTTPException(status_code=503, detail="Bot not initialized")

    _bot.audio_player.set_volume(level / 100.0)
    await _bot.chat_message.send_public(TARGET_CHANNEL, f"🔊 Volume set to {level}% via dashboard")
    return {"message": f"Volume set to {level}%", "volume": level}


@app.post("/api/playback/repeat")
async def set_repeat(mode: str = Query(...), count: int = Query(1, ge=1)):
    """Set repeat mode: 'off', 'count', or 'infinite'."""
    if _bot is None:
        raise HTTPException(status_code=503, detail="Bot not initialized")

    if mode not in ("off", "count", "infinite"):
        raise HTTPException(status_code=400, detail="Invalid mode. Use 'off', 'count', or 'infinite'.")

    if mode == "off":
        _bot.repeat_mode = "off"
        _bot.repeat_remaining = 0
        msg = "🔁 Repeat turned OFF via dashboard"
    elif mode == "count":
        _bot.repeat_mode = "count"
        _bot.repeat_count = count
        _bot.repeat_remaining = count
        msg = f"🔁 Repeat set to {count}x via dashboard"
    elif mode == "infinite":
        _bot.repeat_mode = "infinite"
        _bot.repeat_remaining = -1
        msg = "🔁 INFINITE repeat enabled via dashboard"

    await _bot.chat_message.send_public(TARGET_CHANNEL, msg)
    return {"message": f"Repeat set to {mode}", "mode": mode, "count": count}


# ─── Blacklist ───

@app.get("/api/blacklist")
async def get_blacklist():
    """Get all blacklisted users."""
    if _admin_handler is None:
        raise HTTPException(status_code=503, detail="Admin handler not initialized")

    users = _admin_handler.get_blacklist_list()
    return {"users": sorted(users)}


@app.post("/api/blacklist")
async def add_to_blacklist(username: str = Query(...)):
    """Add a user to the blacklist."""
    if _admin_handler is None:
        raise HTTPException(status_code=503, detail="Admin handler not initialized")

    if not username:
        raise HTTPException(status_code=400, detail="Username is required")

    success = _admin_handler.add_blacklist(username)
    if not success:
        raise HTTPException(status_code=409, detail=f"User '{username}' is already blacklisted")

    msg = f"🚫 @{username} has been blacklisted via dashboard"
    if _bot is not None:
        await _bot.chat_message.send_public(TARGET_CHANNEL, msg)
    return {"message": msg}


@app.delete("/api/blacklist/{username}")
async def remove_from_blacklist(username: str):
    """Remove a user from the blacklist."""
    if _admin_handler is None:
        raise HTTPException(status_code=503, detail="Admin handler not initialized")

    success = _admin_handler.remove_blacklist(username)
    if not success:
        raise HTTPException(status_code=404, detail=f"User '{username}' is not in the blacklist")

    msg = f"✅ @{username} removed from blacklist via dashboard"
    if _bot is not None:
        await _bot.chat_message.send_public(TARGET_CHANNEL, msg)
    return {"message": msg}


# ─── Whitelist ───

@app.get("/api/whitelist")
async def get_whitelist():
    """Get all whitelisted users."""
    if _admin_handler is None:
        raise HTTPException(status_code=503, detail="Admin handler not initialized")

    users = _admin_handler.get_whitelist_list()
    return {"users": sorted(users)}


@app.post("/api/whitelist")
async def add_to_whitelist(username: str = Query(...)):
    """Add a user to the whitelist."""
    if _admin_handler is None:
        raise HTTPException(status_code=503, detail="Admin handler not initialized")

    if not username:
        raise HTTPException(status_code=400, detail="Username is required")

    success = _admin_handler.add_whitelist(username)
    if not success:
        raise HTTPException(status_code=409, detail=f"User '{username}' is already whitelisted")

    msg = f"✅ @{username} added to whitelist via dashboard"
    if _bot is not None:
        await _bot.chat_message.send_public(TARGET_CHANNEL, msg)
    return {"message": msg}


@app.delete("/api/whitelist/{username}")
async def remove_from_whitelist(username: str):
    """Remove a user from the whitelist."""
    if _admin_handler is None:
        raise HTTPException(status_code=503, detail="Admin handler not initialized")

    success = _admin_handler.remove_whitelist(username)
    if not success:
        raise HTTPException(status_code=404, detail=f"User '{username}' is not in the whitelist")

    msg = f"👤 @{username} removed from whitelist via dashboard"
    if _bot is not None:
        await _bot.chat_message.send_public(TARGET_CHANNEL, msg)
    return {"message": msg}


# ─── Playlists ───

@app.get("/api/playlists")
async def get_all_playlists(username: Optional[str] = Query(None)):
    """Get all playlists, optionally filtered by user."""
    if _playlist_manager is None:
        raise HTTPException(status_code=503, detail="Playlist manager not initialized")

    if username:
        playlists = _playlist_manager.get_user_playlists(username)
        return {"user": username, "playlists": [p.to_dict() for p in playlists]}

    # Return all users' playlists
    all_playlists = {}
    for user_file in _playlist_manager.data_dir.glob("*.json"):
        user = user_file.stem
        playlists = _playlist_manager.get_user_playlists(user)
        if playlists:
            all_playlists[user] = [p.to_dict() for p in playlists]

    return {"playlists": all_playlists}


@app.get("/api/playlists/{username}/{playlist_id}")
async def get_playlist(username: str, playlist_id: str):
    """Get a specific playlist."""
    if _playlist_manager is None:
        raise HTTPException(status_code=503, detail="Playlist manager not initialized")

    playlist = _playlist_manager.get_playlist(username, playlist_id)
    if playlist is None:
        raise HTTPException(status_code=404, detail="Playlist not found")

    return playlist.to_dict()


@app.post("/api/playlists")
async def create_playlist(username: str = Query(...), name: str = Query(...)):
    """Create a new playlist for a user."""
    if _playlist_manager is None:
        raise HTTPException(status_code=503, detail="Playlist manager not initialized")

    playlist = _playlist_manager.create_playlist(username, name)
    if playlist is None:
        raise HTTPException(status_code=409, detail=f"Playlist '{name}' already exists for user '{username}'")

    return {"message": f"Playlist '{name}' created", "playlist": playlist.to_dict()}


@app.delete("/api/playlists/{username}/{playlist_id}")
async def delete_playlist(username: str, playlist_id: str):
    """Delete a playlist entirely."""
    if _playlist_manager is None:
        raise HTTPException(status_code=503, detail="Playlist manager not initialized")

    user_playlists = _playlist_manager.get_user_playlists(username)
    found = False
    for pl in user_playlists:
        if pl.id == playlist_id:
            found = True
            break

    if not found:
        raise HTTPException(status_code=404, detail="Playlist not found")

    # Delete by removing from memory and saving
    if username in _playlist_manager._playlists and playlist_id in _playlist_manager._playlists[username]:
        del _playlist_manager._playlists[username][playlist_id]
        _playlist_manager._save_user_playlists(username)

    return {"message": "Playlist deleted"}


@app.post("/api/playlists/{username}/{playlist_name}/songs")
async def add_song_to_playlist(username: str, playlist_name: str, query: str = Query(...)):
    """Add a song to a playlist."""
    if _playlist_manager is None:
        raise HTTPException(status_code=503, detail="Playlist manager not initialized")

    if _bot is None:
        raise HTTPException(status_code=503, detail="Bot not initialized")

    # Find matching file
    file_path = _bot.music_downloader._find_matching_file(query)
    if not file_path:
        raise HTTPException(status_code=404, detail=f"No matching song found for '{query}'")

    playlist = _playlist_manager.get_playlist_by_name(username, playlist_name)
    if not playlist:
        raise HTTPException(status_code=404, detail=f"Playlist '{playlist_name}' not found for user '{username}'")

    success = _playlist_manager.add_song_to_playlist(username, playlist_name, query, file_path, username)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to add song to playlist")

    return {"message": f"Song '{query}' added to '{playlist_name}'"}


@app.delete("/api/playlists/{username}/{playlist_name}/songs/{index_or_name}")
async def remove_song_from_playlist(username: str, playlist_name: str, index_or_name: str):
    """Remove a song from a playlist by index or name."""
    if _playlist_manager is None:
        raise HTTPException(status_code=503, detail="Playlist manager not initialized")

    success = _playlist_manager.remove_song_from_playlist(username, playlist_name, index_or_name)
    if not success:
        raise HTTPException(status_code=404, detail="Song not found in playlist")

    return {"message": "Song removed from playlist"}


# ─── Analytics ───

@app.get("/api/analytics/summary")
async def get_analytics_summary():
    """Get overall analytics summary."""
    if _analytics is None:
        raise HTTPException(status_code=503, detail="Analytics not initialized")

    return {
        "total_requests": _analytics.get_total_requests(),
        "total_plays": _analytics.get_total_plays(),
        "today": _analytics.get_stats_today(),
        "week": _analytics.get_stats_week(),
        "month": _analytics.get_stats_month(),
    }


@app.get("/api/analytics/top-songs")
async def get_top_songs(n: int = Query(10, ge=1, le=100)):
    """Get top N most played songs."""
    if _analytics is None:
        raise HTTPException(status_code=503, detail="Analytics not initialized")

    return {"songs": _analytics.get_top_songs(n)}


@app.get("/api/analytics/top-users")
async def get_top_users(n: int = Query(10, ge=1, le=100)):
    """Get top N most active users."""
    if _analytics is None:
        raise HTTPException(status_code=503, detail="Analytics not initialized")

    return {"users": _analytics.get_top_users(n)}


@app.get("/api/analytics/history")
async def get_history(n: int = Query(20, ge=1, le=100)):
    """Get last N plays from history."""
    if _analytics is None:
        raise HTTPException(status_code=503, detail="Analytics not initialized")

    return {"history": _analytics.get_play_history(n)}


# ─── Library ───

@app.get("/api/library")
async def get_library(limit: int = Query(100, ge=1, le=1000)):
    """List downloaded audio files."""
    files = []
    if os.path.exists(DOWNLOAD_DIR):
        for f in sorted(os.listdir(DOWNLOAD_DIR)):
            if f.lower().endswith((".mp3", ".wav", ".m4a")):
                filepath = os.path.join(DOWNLOAD_DIR, f)
                files.append({
                    "filename": f,
                    "title": os.path.splitext(f)[0],
                    "size": os.path.getsize(filepath),
                })
                if len(files) >= limit:
                    break

    return {"files": files, "total": len(files)}


# ─── Trusted Channels ───

@app.get("/api/trusted-channels")
async def get_trusted_channels():
    """Get all trusted YouTube channels."""
    if _admin_handler is None:
        raise HTTPException(status_code=503, detail="Admin handler not initialized")

    channels = _admin_handler.get_trusted_channels()
    return {"channels": channels}
