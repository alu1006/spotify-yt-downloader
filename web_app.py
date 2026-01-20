#!/usr/bin/env python3
"""
Spotify to YouTube Converter - Web Application
網頁版介面：Spotify 歌單轉換 YouTube 歌單並下載
純記憶體模式 - 不儲存任何資料
"""

from flask import Flask, render_template, request, jsonify
import os
import subprocess
import threading
import asyncio
from pathlib import Path

app = Flask(__name__)

# 記憶體中的歌單資料
current_playlist = {
    'playlist_name': '',
    'playlist_url': '',
    'total_tracks': 0,
    'tracks': []
}

# 狀態追蹤
status = {
    'scraping': False,
    'creating_playlist': False,
    'downloading': False,
    'message': '',
    'progress': 0
}


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/tracks')
def get_tracks():
    """Get current tracks from memory"""
    return jsonify(current_playlist)


@app.route('/api/scrape', methods=['POST'])
def scrape_playlist():
    """Start scraping a Spotify playlist"""
    global current_playlist
    
    data = request.get_json()
    url = data.get('url', '')
    
    if not url or 'spotify.com/playlist/' not in url:
        return jsonify({'error': '請輸入有效的 Spotify 歌單網址'}), 400
    
    if status['scraping']:
        return jsonify({'error': '正在抓取中，請稍候'}), 400
    
    def run_scraper():
        global current_playlist
        status['scraping'] = True
        status['message'] = '正在抓取歌單...'
        
        try:
            # 直接在這裡執行抓取，不透過子程序
            from scraper_memory import scrape_playlist_to_memory
            result = asyncio.run(scrape_playlist_to_memory(url))
            
            if result and result.get('tracks'):
                current_playlist = result
                status['message'] = f"抓取完成！共 {result['total_tracks']} 首歌曲"
            else:
                status['message'] = '抓取失敗：找不到歌曲'
                
        except Exception as e:
            status['message'] = f'錯誤: {e}'
        finally:
            status['scraping'] = False
    
    threading.Thread(target=run_scraper, daemon=True).start()
    return jsonify({'status': 'started'})


@app.route('/api/download', methods=['POST'])
def download_songs():
    """Start downloading all songs"""
    if status['downloading']:
        return jsonify({'error': '正在下載中，請稍候'}), 400
    
    if not current_playlist.get('tracks'):
        return jsonify({'error': '找不到歌曲資料，請先抓取歌單'}), 400
    
    def run_download():
        status['downloading'] = True
        status['message'] = '正在下載歌曲...'
        status['progress'] = 0
        
        try:
            tracks = current_playlist['tracks']
            download_dir = Path('downloads')
            download_dir.mkdir(exist_ok=True)
            
            total = len(tracks)
            success = 0
            
            for i, track in enumerate(tracks):
                artists = ', '.join(track.get('artists', []))
                search_query = track.get('search_query', f"{track['name']} {artists}")
                filename = f"{track['name']} - {artists}"
                filename = "".join(c for c in filename if c not in r'\/:*?"<>|')
                
                status['message'] = f"下載中 [{i+1}/{total}]: {track['name']}"
                status['progress'] = int((i + 1) / total * 100)
                
                try:
                    cmd = [
                        'yt-dlp', '-x', '--audio-format', 'mp3',
                        '--audio-quality', '0',
                        '-o', str(download_dir / f'{filename}.%(ext)s'),
                        '--no-playlist', '--quiet',
                        '--default-search', 'ytsearch',
                        f'ytsearch:{search_query}'
                    ]
                    subprocess.run(cmd, timeout=120)
                    success += 1
                except:
                    pass
            
            status['message'] = f'下載完成！成功: {success}/{total}'
            status['progress'] = 100
            
        except Exception as e:
            status['message'] = f'錯誤: {e}'
        finally:
            status['downloading'] = False
    
    threading.Thread(target=run_download, daemon=True).start()
    return jsonify({'status': 'started'})


@app.route('/api/status')
def get_status():
    """Get current operation status"""
    return jsonify(status)


@app.route('/api/youtube/create', methods=['POST'])
def create_youtube_playlist():
    """Create YouTube playlist"""
    data = request.get_json()
    playlist_name = data.get('name', 'My Playlist')
    
    if status['creating_playlist']:
        return jsonify({'error': '正在建立中，請稍候'}), 400
    
    if not current_playlist.get('tracks'):
        return jsonify({'error': '找不到歌曲資料，請先抓取歌單'}), 400
    
    def run_create():
        status['creating_playlist'] = True
        status['message'] = '正在建立 YouTube 歌單...'
        
        try:
            from youtube_playlist import create_youtube_playlist_from_tracks
            tracks = current_playlist['tracks']
            results = create_youtube_playlist_from_tracks(tracks, playlist_name)
            
            status['message'] = f"完成！成功: {len(results['added'])} 首\n歌單網址: {results['playlist_url']}"
            
        except Exception as e:
            status['message'] = f'錯誤: {e}'
        finally:
            status['creating_playlist'] = False
    
    threading.Thread(target=run_create, daemon=True).start()
    return jsonify({'status': 'started'})


@app.route('/api/clear', methods=['POST'])
def clear_data():
    """Clear current playlist data"""
    global current_playlist
    current_playlist = {
        'playlist_name': '',
        'playlist_url': '',
        'total_tracks': 0,
        'tracks': []
    }
    return jsonify({'status': 'cleared'})


@app.route('/api/open-folder', methods=['POST'])
def open_download_folder():
    """Open the downloads folder in Finder"""
    import subprocess
    download_dir = Path('downloads')
    download_dir.mkdir(exist_ok=True)
    
    try:
        # macOS: use 'open' command
        subprocess.run(['open', str(download_dir.absolute())])
        return jsonify({'status': 'opened', 'path': str(download_dir.absolute())})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    app.run(debug=True, port=5000)

