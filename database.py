"""
SQLite Database Manager for Spotify Tracks
使用 SQLite 資料庫取代 JSON 儲存歌單資料
"""

import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Optional

DB_PATH = Path(__file__).parent / 'spotify_tracks.db'


def get_connection():
    """Get database connection"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 歌單資訊表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 歌曲資訊表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_id INTEGER,
            track_index INTEGER,
            name TEXT NOT NULL,
            artists TEXT,
            search_query TEXT,
            FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()


def save_playlist(playlist_name: str, playlist_url: str, tracks: List[Dict]) -> int:
    """
    Save playlist and tracks to database
    
    Args:
        playlist_name: Name of the playlist
        playlist_url: Spotify URL of the playlist
        tracks: List of track dictionaries
        
    Returns:
        playlist_id: ID of the saved playlist
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 刪除舊的相同 URL 歌單（如果存在）
        cursor.execute('SELECT id FROM playlists WHERE url = ?', (playlist_url,))
        existing = cursor.fetchone()
        if existing:
            cursor.execute('DELETE FROM tracks WHERE playlist_id = ?', (existing['id'],))
            cursor.execute('DELETE FROM playlists WHERE id = ?', (existing['id'],))
        
        # 插入新歌單
        cursor.execute('''
            INSERT INTO playlists (name, url) VALUES (?, ?)
        ''', (playlist_name, playlist_url))
        playlist_id = cursor.lastrowid
        
        # 插入歌曲
        for i, track in enumerate(tracks):
            artists = ', '.join(track.get('artists', []))
            cursor.execute('''
                INSERT INTO tracks (playlist_id, track_index, name, artists, search_query)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                playlist_id,
                i + 1,
                track.get('name', ''),
                artists,
                track.get('search_query', f"{track.get('name', '')} {artists}")
            ))
        
        conn.commit()
        print(f"✅ 歌單已儲存至資料庫: {playlist_name} ({len(tracks)} 首歌曲)")
        return playlist_id
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 儲存歌單失敗: {e}")
        raise
    finally:
        conn.close()


def get_current_playlist() -> Dict:
    """
    Get the most recent playlist with tracks
    
    Returns:
        Dictionary with playlist info and tracks
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 取得最新的歌單
        cursor.execute('''
            SELECT id, name, url, created_at FROM playlists 
            ORDER BY created_at DESC LIMIT 1
        ''')
        playlist = cursor.fetchone()
        
        if not playlist:
            return {
                'playlist_name': '',
                'playlist_url': '',
                'total_tracks': 0,
                'tracks': []
            }
        
        # 取得歌曲
        cursor.execute('''
            SELECT track_index, name, artists, search_query 
            FROM tracks WHERE playlist_id = ?
            ORDER BY track_index
        ''', (playlist['id'],))
        
        tracks = []
        for row in cursor.fetchall():
            artists_list = [a.strip() for a in row['artists'].split(',') if a.strip()]
            tracks.append({
                'index': row['track_index'],
                'name': row['name'],
                'artists': artists_list,
                'search_query': row['search_query']
            })
        
        return {
            'playlist_name': playlist['name'],
            'playlist_url': playlist['url'],
            'total_tracks': len(tracks),
            'tracks': tracks
        }
        
    finally:
        conn.close()


def get_all_playlists() -> List[Dict]:
    """Get all saved playlists"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT p.id, p.name, p.url, p.created_at,
                   COUNT(t.id) as track_count
            FROM playlists p
            LEFT JOIN tracks t ON p.id = t.playlist_id
            GROUP BY p.id
            ORDER BY p.created_at DESC
        ''')
        
        return [dict(row) for row in cursor.fetchall()]
        
    finally:
        conn.close()


def get_playlist_by_id(playlist_id: int) -> Optional[Dict]:
    """Get specific playlist by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM playlists WHERE id = ?', (playlist_id,))
        playlist = cursor.fetchone()
        
        if not playlist:
            return None
        
        cursor.execute('''
            SELECT track_index, name, artists, search_query 
            FROM tracks WHERE playlist_id = ?
            ORDER BY track_index
        ''', (playlist_id,))
        
        tracks = []
        for row in cursor.fetchall():
            artists_list = [a.strip() for a in row['artists'].split(',') if a.strip()]
            tracks.append({
                'index': row['track_index'],
                'name': row['name'],
                'artists': artists_list,
                'search_query': row['search_query']
            })
        
        return {
            'playlist_name': playlist['name'],
            'playlist_url': playlist['url'],
            'total_tracks': len(tracks),
            'tracks': tracks
        }
        
    finally:
        conn.close()


def clear_all():
    """Clear all data from database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM tracks')
        cursor.execute('DELETE FROM playlists')
        conn.commit()
        print("✅ 資料庫已清空")
    finally:
        conn.close()


# 初始化資料庫
init_db()
