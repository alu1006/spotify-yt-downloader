"""
Spotify API Client
Uses official Spotify API via spotipy to fetch playlist data
"""

import os
import json
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


def get_spotify_client(client_id: str, client_secret: str) -> spotipy.Spotify:
    """
    Create an authenticated Spotify client
    
    Args:
        client_id: Spotify API client ID
        client_secret: Spotify API client secret
        
    Returns:
        Authenticated Spotify client
    """
    client_credentials_manager = SpotifyClientCredentials(
        client_id=client_id,
        client_secret=client_secret
    )
    return spotipy.Spotify(client_credentials_manager=client_credentials_manager)


def extract_playlist_id(playlist_url: str) -> str:
    """Extract playlist ID from Spotify URL"""
    # Handle various URL formats
    if 'playlist/' in playlist_url:
        playlist_id = playlist_url.split('playlist/')[1]
        # Remove query parameters
        if '?' in playlist_id:
            playlist_id = playlist_id.split('?')[0]
        return playlist_id
    return playlist_url


def fetch_playlist_tracks(client_id: str, client_secret: str, playlist_url: str) -> dict:
    """
    Fetch all tracks from a Spotify playlist using the API
    
    Args:
        client_id: Spotify API client ID
        client_secret: Spotify API client secret
        playlist_url: Spotify playlist URL
        
    Returns:
        Dictionary with playlist info and tracks
    """
    sp = get_spotify_client(client_id, client_secret)
    playlist_id = extract_playlist_id(playlist_url)
    
    print(f"正在使用 Spotify API 抓取歌單...")
    
    # Get playlist info
    playlist = sp.playlist(playlist_id)
    playlist_name = playlist['name']
    total_tracks = playlist['tracks']['total']
    
    print(f"歌單名稱: {playlist_name}")
    print(f"總歌曲數: {total_tracks}")
    
    # Fetch all tracks (paginated)
    tracks = []
    results = playlist['tracks']
    
    while True:
        for i, item in enumerate(results['items']):
            track = item.get('track')
            if track is None:
                continue
                
            track_name = track.get('name', 'Unknown')
            artists = [artist['name'] for artist in track.get('artists', [])]
            
            track_info = {
                'index': len(tracks) + 1,
                'name': track_name,
                'artists': artists,
                'search_query': f"{track_name} {' '.join(artists)}",
                'spotify_id': track.get('id'),
                'duration_ms': track.get('duration_ms')
            }
            tracks.append(track_info)
            print(f"  [{track_info['index']}] {track_name} - {', '.join(artists)}")
        
        # Check if there are more tracks
        if results['next']:
            results = sp.next(results)
        else:
            break
    
    result = {
        'playlist_name': playlist_name,
        'playlist_url': playlist_url,
        'total_tracks': len(tracks),
        'tracks': tracks
    }
    
    # Save to JSON file
    output_file = 'spotify_tracks.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n歌曲資料已儲存至 {output_file}")
    
    return result


if __name__ == '__main__':
    import sys
    
    # Get credentials from environment or prompt
    client_id = os.environ.get('SPOTIFY_CLIENT_ID')
    client_secret = os.environ.get('SPOTIFY_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("請設定 Spotify API 憑證:")
        client_id = input("Client ID: ").strip()
        client_secret = input("Client Secret: ").strip()
    
    if len(sys.argv) > 1:
        playlist_url = sys.argv[1]
    else:
        playlist_url = "https://open.spotify.com/playlist/7Efaw5INyn3zbHlarlNH2Q"
    
    result = fetch_playlist_tracks(client_id, client_secret, playlist_url)
    print(f"\n完成！共抓取 {result['total_tracks']} 首歌曲")
