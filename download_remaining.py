#!/usr/bin/env python3
"""
Download remaining songs that weren't added to YouTube playlist
下載剩餘還沒加入 YouTube 歌單的歌曲
Uses yt-dlp search feature (no API needed)
"""

import json
import os
import subprocess
from pathlib import Path


def download_remaining():
    # Load all tracks
    with open('spotify_tracks.json', 'r', encoding='utf-8') as f:
        all_tracks = json.load(f)['tracks']
    
    # Load results to see what was already added
    with open('youtube_results.json', 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    # Find tracks that weren't added
    added_names = set(t['track']['name'] for t in results['added'])
    remaining = [t for t in all_tracks if t['name'] not in added_names]
    
    print(f"準備下載剩餘 {len(remaining)} 首歌曲\n")
    
    # Create download directory
    download_dir = Path('downloads')
    download_dir.mkdir(exist_ok=True)
    
    success = 0
    failed = []
    
    for i, track in enumerate(remaining):
        artists = ', '.join(track['artists']) if track['artists'] else 'Unknown'
        search_query = track['search_query']
        
        # Create filename
        filename = f"{track['name']} - {artists}"
        filename = "".join(c for c in filename if c not in r'\/:*?"<>|')
        
        print(f"[{i+1}/{len(remaining)}] 搜尋下載: {track['name']} - {artists}")
        
        try:
            # Use yt-dlp with search
            cmd = [
                'yt-dlp',
                '-x',  # Extract audio
                '--audio-format', 'mp3',
                '--audio-quality', '0',
                '-o', str(download_dir / f'{filename}.%(ext)s'),
                '--no-playlist',
                '--quiet',
                '--progress',
                '--default-search', 'ytsearch',  # Use YouTube search
                f'ytsearch:{search_query}'  # Search query
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print(f"  ✓ 完成")
                success += 1
            else:
                print(f"  ✗ 失敗")
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
    download_remaining()
