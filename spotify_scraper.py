"""
Spotify Playlist Scraper
Scrapes song information from public Spotify playlists using Playwright
"""

import asyncio
from playwright.async_api import async_playwright
from database import save_playlist


async def scrape_spotify_playlist(playlist_url: str, headless: bool = False) -> dict:
    """
    Scrape a Spotify playlist and return song information.
    """
    tracks = []
    playlist_name = ""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 900}
        )
        page = await context.new_page()
        
        print(f"正在載入 Spotify 歌單...")
        await page.goto(playlist_url)
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)
        
        # Get playlist name
        try:
            playlist_name_elem = await page.query_selector('h1[data-testid="entityTitle"]')
            if playlist_name_elem:
                playlist_name = await playlist_name_elem.inner_text()
            else:
                title = await page.title()
                playlist_name = title.split(' - playlist by')[0] if ' - playlist by' in title else "Spotify Playlist"
        except:
            playlist_name = "Spotify Playlist"
        
        print(f"歌單名稱: {playlist_name}")
        print("正在載入所有歌曲...")
        
        # Scroll to load all tracks
        last_count = 0
        no_change = 0
        
        while no_change < 15:
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(0.5)
            await page.keyboard.press('End')
            await asyncio.sleep(0.5)
            
            rows = await page.query_selector_all('[data-testid="tracklist-row"]')
            current = len(rows)
            
            if current == last_count:
                no_change += 1
                for _ in range(3):
                    await page.keyboard.press('PageDown')
                    await asyncio.sleep(0.2)
            else:
                no_change = 0
                last_count = current
                print(f"  已載入 {current} 首歌曲...")
        
        print(f"\n載入完成，開始收集 {last_count} 首歌曲...")
        
        # Go back to top
        await page.keyboard.press('Home')
        await asyncio.sleep(1)
        await page.evaluate('window.scrollTo(0, 0)')
        await asyncio.sleep(1)
        
        # Collect all tracks by scrolling through
        seen_tracks = set()  # Track unique identifiers
        
        for scroll_round in range(100):
            rows = await page.query_selector_all('[data-testid="tracklist-row"]')
            
            for row in rows:
                try:
                    # Get track name - try multiple selectors
                    track_name = None
                    
                    # Try: div inside the link
                    elem = await row.query_selector('a[data-testid="internal-track-link"] div')
                    if elem:
                        track_name = await elem.inner_text()
                    
                    # Fallback: the link itself
                    if not track_name:
                        elem = await row.query_selector('a[data-testid="internal-track-link"]')
                        if elem:
                            track_name = await elem.inner_text()
                    
                    if not track_name:
                        continue
                    
                    track_name = track_name.strip()
                    
                    # Get artists
                    artist_elems = await row.query_selector_all('span a[href^="/artist/"]')
                    if not artist_elems:
                        artist_elems = await row.query_selector_all('a[href^="/artist/"]')
                    
                    artists = []
                    for ae in artist_elems:
                        name = await ae.inner_text()
                        if name and name.strip() and name.strip() not in artists:
                            artists.append(name.strip())
                    
                    # Create unique key
                    key = f"{track_name}|{'|'.join(artists)}"
                    
                    if key not in seen_tracks:
                        seen_tracks.add(key)
                        tracks.append({
                            'index': len(tracks) + 1,
                            'name': track_name,
                            'artists': artists,
                            'search_query': f"{track_name} {' '.join(artists)}"
                        })
                        print(f"  [{len(tracks)}] {track_name} - {', '.join(artists)}")
                        
                except Exception as e:
                    continue
            
            # Check if we have all tracks
            if len(tracks) >= last_count:
                break
            
            # Scroll down
            for _ in range(2):
                await page.keyboard.press('PageDown')
                await asyncio.sleep(0.3)
        
        await browser.close()
    
    result = {
        'playlist_name': playlist_name,
        'playlist_url': playlist_url,
        'total_tracks': len(tracks),
        'tracks': tracks
    }
    
    # 儲存到 SQLite 資料庫
    save_playlist(playlist_name, playlist_url, tracks)
    
    return result


def scrape_playlist(playlist_url: str) -> dict:
    """Synchronous wrapper for the async scraper"""
    return asyncio.run(scrape_spotify_playlist(playlist_url))


if __name__ == '__main__':
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://open.spotify.com/playlist/7Efaw5INyn3zbHlarlNH2Q"
    result = scrape_playlist(url)
    print(f"\n完成！共抓取 {result['total_tracks']} 首歌曲")
