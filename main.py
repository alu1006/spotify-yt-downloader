#!/usr/bin/env python3
"""
Spotify to YouTube Playlist Converter
主程式：抓取 Spotify 歌單並建立 YouTube 歌單
支援 Spotify API 和網頁爬蟲兩種方式
"""

import json
import os
import sys


def main():
    # Default playlist URL
    default_url = "https://open.spotify.com/playlist/7Efaw5INyn3zbHlarlNH2Q?si=c2d053d10ef04a4e"
    
    # Get playlist URL from argument or use default
    if len(sys.argv) > 1:
        playlist_url = sys.argv[1]
    else:
        playlist_url = default_url
        print(f"使用預設歌單: {playlist_url}")
    
    print("=" * 60)
    print("Spotify to YouTube 歌單轉換工具")
    print("=" * 60)
    
    # Step 1: Choose method and scrape Spotify playlist
    print("\n📱 步驟 1: 抓取 Spotify 歌單")
    print("-" * 40)
    
    # Check if we already have scraped data
    use_existing = False
    if os.path.exists('spotify_tracks.json'):
        print("發現已存在的歌曲資料")
        with open('spotify_tracks.json', 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        print(f"現有資料: {existing_data['total_tracks']} 首歌曲")
        choice = input("輸入 'y' 重新抓取，或按 Enter 使用現有資料: ").strip().lower()
        if choice != 'y':
            spotify_data = existing_data
            use_existing = True
    
    if not use_existing:
        # Ask which method to use
        print("\n選擇抓取方式:")
        print("  1. Spotify API (需要 Client ID 和 Client Secret)")
        print("  2. 網頁爬蟲 (不需要 API 憑證)")
        method = input("請選擇 (1/2): ").strip()
        
        if method == '1':
            # Use Spotify API
            from spotify_api import fetch_playlist_tracks
            
            client_id = os.environ.get('SPOTIFY_CLIENT_ID')
            client_secret = os.environ.get('SPOTIFY_CLIENT_SECRET')
            
            if not client_id:
                client_id = input("請輸入 Spotify Client ID: ").strip()
            if not client_secret:
                client_secret = input("請輸入 Spotify Client Secret: ").strip()
            
            spotify_data = fetch_playlist_tracks(client_id, client_secret, playlist_url)
        else:
            # Use web scraper
            from spotify_scraper import scrape_playlist
            spotify_data = scrape_playlist(playlist_url)
    
    if not spotify_data['tracks']:
        print("錯誤：無法抓取任何歌曲！")
        sys.exit(1)
    
    print(f"\n抓取完成！共 {spotify_data['total_tracks']} 首歌曲")
    
    # Step 2: Create YouTube playlist
    print("\n🎬 步驟 2: 建立 YouTube 歌單")
    print("-" * 40)
    
    from youtube_playlist import create_youtube_playlist_from_tracks
    
    playlist_name = spotify_data.get('playlist_name', 'Spotify Playlist')
    tracks = spotify_data['tracks']
    
    print(f"歌單名稱: {playlist_name}")
    print(f"歌曲數量: {len(tracks)}")
    
    confirm = input("\n確定要建立 YouTube 歌單嗎？(y/n): ").strip().lower()
    if confirm != 'y':
        print("已取消操作")
        sys.exit(0)
    
    # Create YouTube playlist
    results = create_youtube_playlist_from_tracks(tracks, playlist_name)
    
    print("\n" + "=" * 60)
    print("✅ 轉換完成！")
    print("=" * 60)
    print(f"\nYouTube 歌單網址:")
    print(f"  {results['playlist_url']}")
    
    if results['not_found']:
        print(f"\n⚠️  以下 {len(results['not_found'])} 首歌曲找不到對應的 YouTube 影片:")
        for track in results['not_found']:
            print(f"   - {track.get('name', 'Unknown')} - {', '.join(track.get('artists', []))}")


if __name__ == '__main__':
    main()
