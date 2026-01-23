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


@app.route('/api/download-youtube', methods=['POST'])
def download_youtube():
    """Download from YouTube URL (single video or playlist)"""
    if status['downloading']:
        return jsonify({'error': '正在下載中，請稍候'}), 400
    
    data = request.get_json()
    url = data.get('url', '')
    
    if not url or ('youtube.com' not in url and 'youtu.be' not in url):
        return jsonify({'error': '請輸入有效的 YouTube 網址'}), 400
    
    def run_yt_download():
        status['downloading'] = True
        status['message'] = '正在下載 YouTube...'
        status['progress'] = 0
        
        try:
            download_dir = Path('downloads')
            download_dir.mkdir(exist_ok=True)
            
            # Check if it's a playlist
            is_playlist = 'list=' in url
            
            if is_playlist:
                status['message'] = '正在下載 YouTube 播放清單...'
                cmd = [
                    'yt-dlp', '-x', '--audio-format', 'mp3',
                    '--audio-quality', '0',
                    '-o', str(download_dir / '%(title)s.%(ext)s'),
                    '--yes-playlist',
                    url
                ]
            else:
                status['message'] = '正在下載 YouTube 影片...'
                cmd = [
                    'yt-dlp', '-x', '--audio-format', 'mp3',
                    '--audio-quality', '0',
                    '-o', str(download_dir / '%(title)s.%(ext)s'),
                    '--no-playlist',
                    url
                ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                status['message'] = '下載完成！'
            else:
                status['message'] = f'下載失敗: {result.stderr[:200]}'
            
            status['progress'] = 100
            
        except subprocess.TimeoutExpired:
            status['message'] = '下載逾時'
        except Exception as e:
            status['message'] = f'錯誤: {e}'
        finally:
            status['downloading'] = False
    
    threading.Thread(target=run_yt_download, daemon=True).start()
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


# ============ MP3 Editor APIs ============

@app.route('/editor')
def editor():
    """MP3 Editor page"""
    return render_template('editor.html')


@app.route('/api/files')
def list_files():
    """List all MP3 files in downloads folder"""
    download_dir = Path('downloads')
    download_dir.mkdir(exist_ok=True)
    
    files = []
    for f in download_dir.glob('*.mp3'):
        stat = f.stat()
        files.append({
            'name': f.name,
            'size': stat.st_size,
            'modified': stat.st_mtime
        })
    
    # Sort by modification time (newest first)
    files.sort(key=lambda x: x['modified'], reverse=True)
    return jsonify({'files': files})


@app.route('/api/audio/<filename>')
def serve_audio(filename):
    """Serve audio file for playback"""
    from flask import send_from_directory
    download_dir = Path('downloads').absolute()
    return send_from_directory(download_dir, filename)


@app.route('/api/audio-info/<filename>')
def get_audio_info(filename):
    """Get audio duration using ffprobe"""
    filepath = Path('downloads') / filename
    
    if not filepath.exists():
        return jsonify({'error': '檔案不存在'}), 404
    
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', str(filepath)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            import json
            info = json.loads(result.stdout)
            duration = float(info.get('format', {}).get('duration', 0))
            return jsonify({
                'duration': duration,
                'filename': filename
            })
        else:
            return jsonify({'error': 'ffprobe failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/trim', methods=['POST'])
def trim_audio():
    """Trim audio file"""
    data = request.get_json()
    filename = data.get('filename', '')
    start = data.get('start', 0)
    end = data.get('end', 0)
    
    if not filename:
        return jsonify({'error': '請選擇檔案'}), 400
    
    filepath = Path('downloads') / filename
    if not filepath.exists():
        return jsonify({'error': '檔案不存在'}), 404
    
    # Generate output filename
    stem = filepath.stem
    output_name = f"{stem}_trimmed.mp3"
    output_path = Path('downloads') / output_name
    
    # If already exists, add number
    counter = 1
    while output_path.exists():
        output_name = f"{stem}_trimmed_{counter}.mp3"
        output_path = Path('downloads') / output_name
        counter += 1
    
    try:
        duration = end - start
        cmd = [
            'ffmpeg', '-y', '-i', str(filepath),
            '-ss', str(start), '-t', str(duration),
            '-acodec', 'libmp3lame', '-q:a', '2',
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            return jsonify({
                'status': 'success',
                'output': output_name,
                'message': f'剪輯完成！儲存為 {output_name}'
            })
        else:
            return jsonify({'error': f'ffmpeg error: {result.stderr[:200]}'}), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({'error': '剪輯逾時'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/delete', methods=['POST'])
def delete_file():
    """Delete a file"""
    data = request.get_json()
    filename = data.get('filename', '')
    
    if not filename:
        return jsonify({'error': '請選擇檔案'}), 400
    
    filepath = Path('downloads') / filename
    if not filepath.exists():
        return jsonify({'error': '檔案不存在'}), 404
    
    try:
        filepath.unlink()
        return jsonify({'status': 'deleted', 'message': f'已刪除 {filename}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    app.run(debug=True, port=5000)


