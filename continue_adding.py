#!/usr/bin/env python3
"""
Continue adding remaining songs to YouTube playlist
繼續新增剩餘歌曲到 YouTube 歌單
"""

import json
from youtube_playlist import (
    get_authenticated_service,
    search_youtube_video,
    add_video_to_playlist,
    SEARCH_DELAY
)
import time


def continue_adding():
    # Load results to see what's missing
    with open('youtube_results.json', 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    # Load all tracks
    with open('spotify_tracks.json', 'r', encoding='utf-8') as f:
        all_tracks = json.load(f)['tracks']
    
    playlist_id = results['playlist_id']
    playlist_url = results['playlist_url']
    
    # Find tracks that weren't added
    added_names = set(t['track']['name'] for t in results['added'])
    not_found = results['not_found']
    
    remaining = []
    for track in all_tracks:
        if track['name'] not in added_names:
            remaining.append(track)
    
    print(f"歌單: {playlist_url}")
    print(f"已新增: {len(results['added'])} 首")
    print(f"剩餘: {len(remaining)} 首")
    
    if not remaining:
        print("\n所有歌曲都已新增完成！")
        return
    
    confirm = input(f"\n要繼續新增 {len(remaining)} 首歌曲嗎？(y/n): ").strip().lower()
    if confirm != 'y':
        print("已取消")
        return
    
    print("\n正在連接 YouTube API...")
    youtube = get_authenticated_service()
    print("連接成功！\n")
    
    newly_added = []
    still_not_found = []
    
    for i, track in enumerate(remaining):
        query = track['search_query']
        print(f"[{i+1}/{len(remaining)}] 搜尋: {query}")
        
        video_id = search_youtube_video(youtube, query)
        
        if video_id:
            if add_video_to_playlist(youtube, playlist_id, video_id):
                print(f"  ✓ 已新增: https://www.youtube.com/watch?v={video_id}")
                newly_added.append({'track': track, 'video_id': video_id})
                results['added'].append({'track': track, 'video_id': video_id})
            else:
                print(f"  ✗ 新增失敗")
                still_not_found.append(track)
        else:
            print(f"  ✗ 找不到影片")
            still_not_found.append(track)
        
        time.sleep(SEARCH_DELAY)
    
    # Update results file
    results['not_found'] = still_not_found
    with open('youtube_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*50}")
    print(f"本次新增: {len(newly_added)} 首")
    print(f"總共新增: {len(results['added'])} 首")
    print(f"找不到: {len(still_not_found)} 首")
    print(f"\n歌單網址: {playlist_url}")


if __name__ == '__main__':
    continue_adding()
