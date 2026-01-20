"""
YouTube Playlist Creator
Creates a YouTube playlist and adds videos by searching for songs
"""

import os
import json
import pickle
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


# YouTube API scopes
SCOPES = ['https://www.googleapis.com/auth/youtube']

# Rate limiting
import time
SEARCH_DELAY = 1  # seconds between searches to avoid rate limiting


def get_authenticated_service():
    """Authenticate and return YouTube API service"""
    credentials = None
    
    # Token file stores the user's access and refresh tokens
    token_file = 'token.pickle'
    
    # Check if we have saved credentials
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            credentials = pickle.load(token)
    
    # If no valid credentials, let the user log in
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            if not os.path.exists('client_secret.json'):
                raise FileNotFoundError(
                    "找不到 client_secret.json 檔案！\n"
                    "請從 Google Cloud Console 下載 OAuth 憑證並放到此目錄"
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES
            )
            credentials = flow.run_local_server(port=8080)
        
        # Save credentials for next run
        with open(token_file, 'wb') as token:
            pickle.dump(credentials, token)
    
    return build('youtube', 'v3', credentials=credentials)


def search_youtube_video(youtube, query: str) -> str:
    """
    Search for a video on YouTube and return its ID
    
    Args:
        youtube: YouTube API service
        query: Search query string
        
    Returns:
        Video ID or None if not found
    """
    try:
        search_response = youtube.search().list(
            q=query,
            part='snippet',
            maxResults=1,
            type='video',
            videoCategoryId='10'  # Music category
        ).execute()
        
        if search_response['items']:
            video = search_response['items'][0]
            return video['id']['videoId']
        
    except HttpError as e:
        print(f"搜尋錯誤: {e}")
    
    return None


def create_playlist(youtube, title: str, description: str = "") -> str:
    """
    Create a new YouTube playlist
    
    Args:
        youtube: YouTube API service
        title: Playlist title
        description: Playlist description
        
    Returns:
        Playlist ID
    """
    try:
        playlist = youtube.playlists().insert(
            part='snippet,status',
            body={
                'snippet': {
                    'title': title,
                    'description': description
                },
                'status': {
                    'privacyStatus': 'private'  # Start as private
                }
            }
        ).execute()
        
        return playlist['id']
        
    except HttpError as e:
        print(f"建立歌單錯誤: {e}")
        raise


def add_video_to_playlist(youtube, playlist_id: str, video_id: str) -> bool:
    """
    Add a video to a playlist
    
    Args:
        youtube: YouTube API service
        playlist_id: Target playlist ID
        video_id: Video ID to add
        
    Returns:
        True if successful, False otherwise
    """
    try:
        youtube.playlistItems().insert(
            part='snippet',
            body={
                'snippet': {
                    'playlistId': playlist_id,
                    'resourceId': {
                        'kind': 'youtube#video',
                        'videoId': video_id
                    }
                }
            }
        ).execute()
        return True
        
    except HttpError as e:
        if 'quotaExceeded' in str(e):
            print("API 配額已用完，請明天再試")
            raise
        print(f"新增影片錯誤: {e}")
        return False


def create_youtube_playlist_from_tracks(tracks: list, playlist_name: str) -> dict:
    """
    Create a YouTube playlist from a list of tracks
    
    Args:
        tracks: List of track dictionaries with 'search_query' key
        playlist_name: Name for the new playlist
        
    Returns:
        Dictionary with results
    """
    print("\n正在連接 YouTube API...")
    youtube = get_authenticated_service()
    print("YouTube 連接成功！")
    
    # Create the playlist
    print(f"\n正在建立歌單: {playlist_name}")
    description = f"從 Spotify 轉換的歌單，共 {len(tracks)} 首歌曲"
    playlist_id = create_playlist(youtube, playlist_name, description)
    print(f"歌單已建立！ID: {playlist_id}")
    
    # Search and add each track
    results = {
        'playlist_id': playlist_id,
        'playlist_url': f'https://www.youtube.com/playlist?list={playlist_id}',
        'added': [],
        'not_found': [],
        'errors': []
    }
    
    total = len(tracks)
    for i, track in enumerate(tracks):
        query = track.get('search_query', f"{track.get('name', '')} {' '.join(track.get('artists', []))}")
        print(f"\n[{i+1}/{total}] 搜尋: {query}")
        
        video_id = search_youtube_video(youtube, query)
        
        if video_id:
            if add_video_to_playlist(youtube, playlist_id, video_id):
                print(f"  ✓ 已新增: https://www.youtube.com/watch?v={video_id}")
                results['added'].append({
                    'track': track,
                    'video_id': video_id
                })
            else:
                print(f"  ✗ 新增失敗")
                results['errors'].append(track)
        else:
            print(f"  ✗ 找不到影片")
            results['not_found'].append(track)
        
        # Rate limiting
        time.sleep(SEARCH_DELAY)
    
    # Summary
    print(f"\n{'='*50}")
    print(f"完成！")
    print(f"成功新增: {len(results['added'])} 首")
    print(f"找不到: {len(results['not_found'])} 首")
    print(f"錯誤: {len(results['errors'])} 首")
    print(f"\n歌單網址: {results['playlist_url']}")
    
    # Save results
    with open('youtube_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"結果已儲存至 youtube_results.json")
    
    return results


if __name__ == '__main__':
    # Test with sample data
    sample_tracks = [
        {'name': 'Shape of You', 'artists': ['Ed Sheeran'], 'search_query': 'Shape of You Ed Sheeran'},
    ]
    create_youtube_playlist_from_tracks(sample_tracks, "Test Playlist")
