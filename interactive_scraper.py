"""
Interactive Spotify Playlist Scraper
Opens browser and waits for user to scroll, then collects all tracks
"""

import asyncio
import json
from playwright.async_api import async_playwright


async def interactive_scrape(playlist_url: str) -> dict:
    """
    Open browser for user to manually scroll, then collect tracks.
    """
    tracks = []
    playlist_name = ""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 900}
        )
        page = await context.new_page()
        
        print(f"正在載入 Spotify 歌單...")
        await page.goto(playlist_url)
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)
        
        # Get playlist name
        try:
            elem = await page.query_selector('h1[data-testid="entityTitle"]')
            if elem:
                playlist_name = await elem.inner_text()
            else:
                title = await page.title()
                playlist_name = title.split(' - playlist by')[0] if ' - playlist by' in title else "Spotify Playlist"
        except:
            playlist_name = "Spotify Playlist"
        
        print(f"\n歌單名稱: {playlist_name}")
        print("\n" + "=" * 50)
        print("請在瀏覽器中手動滾動到歌單底部")
        print("確保所有歌曲都已載入後，回到這裡按 Enter")
        print("=" * 50)
        
        input("\n按 Enter 開始收集歌曲...")
        
        print("\n正在收集歌曲資訊...")
        
        # Scroll back to top
        await page.evaluate('window.scrollTo(0, 0)')
        await asyncio.sleep(1)
        
        # Collect tracks by scrolling through
        seen = set()
        last_count = 0
        no_change = 0
        
        while no_change < 20:
            rows = await page.query_selector_all('[data-testid="tracklist-row"]')
            
            for row in rows:
                try:
                    # Get track name
                    track_name = None
                    elem = await row.query_selector('a[data-testid="internal-track-link"] div')
                    if elem:
                        track_name = await elem.inner_text()
                    if not track_name:
                        elem = await row.query_selector('a[data-testid="internal-track-link"]')
                        if elem:
                            track_name = await elem.inner_text()
                    
                    if not track_name:
                        continue
                    
                    track_name = track_name.strip()
                    
                    # Get artists
                    artist_elems = await row.query_selector_all('a[href^="/artist/"]')
                    artists = []
                    for ae in artist_elems:
                        name = await ae.inner_text()
                        if name and name.strip() and name.strip() not in artists:
                            artists.append(name.strip())
                    
                    key = f"{track_name}|{'|'.join(artists)}"
                    
                    if key not in seen:
                        seen.add(key)
                        tracks.append({
                            'index': len(tracks) + 1,
                            'name': track_name,
                            'artists': artists,
                            'search_query': f"{track_name} {' '.join(artists)}"
                        })
                        print(f"  [{len(tracks)}] {track_name} - {', '.join(artists)}")
                except:
                    continue
            
            if len(tracks) == last_count:
                no_change += 1
            else:
                no_change = 0
                last_count = len(tracks)
            
            # Scroll down
            await page.keyboard.press('PageDown')
            await asyncio.sleep(0.3)
        
        await browser.close()
    
    result = {
        'playlist_name': playlist_name,
        'playlist_url': playlist_url,
        'total_tracks': len(tracks),
        'tracks': tracks
    }
    
    with open('spotify_tracks.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n歌曲資料已儲存至 spotify_tracks.json")
    
    return result


if __name__ == '__main__':
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://open.spotify.com/playlist/7Efaw5INyn3zbHlarlNH2Q"
    result = asyncio.run(interactive_scrape(url))
    print(f"\n完成！共抓取 {result['total_tracks']} 首歌曲")
