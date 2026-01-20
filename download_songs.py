#!/usr/bin/env python3
"""
Download songs from YouTube using yt-dlp
從 YouTube 下載歌曲
"""

import json
import os
import subprocess
from pathlib import Path


def download_songs():
    # Load results
    with open('youtube_results.json', 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    added_tracks = results['added']
    print(f"準備下載 {len(added_tracks)} 首歌曲\n")
    
    # Create download directory
    download_dir = Path('downloads')
    download_dir.mkdir(exist_ok=True)
    
    success = 0
    failed = []
    
    for i, item in enumerate(added_tracks):
        track = item['track']
        video_id = item['video_id']
        
        # Create filename
        artists = ', '.join(track['artists']) if track['artists'] else 'Unknown'
        filename = f"{track['name']} - {artists}"
        # Clean filename
        filename = "".join(c for c in filename if c not in r'\/:*?"<>|')
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        print(f"[{i+1}/{len(added_tracks)}] 下載: {track['name']} - {artists}")
        
        try:
            # Use yt-dlp to download audio
            cmd = [
                'yt-dlp',
                '-x',  # Extract audio
                '--audio-format', 'mp3',
                '--audio-quality', '0',  # Best quality
                '-o', str(download_dir / f'{filename}.%(ext)s'),
                '--no-playlist',
                '--quiet',
                '--progress',
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print(f"  ✓ 完成")
                success += 1
            else:
                print(f"  ✗ 失敗: {result.stderr[:100] if result.stderr else 'Unknown error'}")
                failed.append(track['name'])
                
        except subprocess.TimeoutExpired:
            print(f"  ✗ 逾時")
            failed.append(track['name'])
        except Exception as e:
            print(f"  ✗ 錯誤: {e}")
            failed.append(track['name'])
    
    print(f"\n{'='*50}")
    print(f"下載完成！")
    print(f"成功: {success} 首")
    print(f"失敗: {len(failed)} 首")
    print(f"\n檔案位置: {download_dir.absolute()}")
    
    if failed:
        print(f"\n失敗的歌曲:")
        for name in failed:
            print(f"  - {name}")


if __name__ == '__main__':
    download_songs()
