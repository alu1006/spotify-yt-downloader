"""
Spotify Playlist Scraper - Memory Only Version
抓取 Spotify 歌單，只回傳資料不儲存
"""

import asyncio
from playwright.async_api import async_playwright


async def scrape_playlist_to_memory(playlist_url: str) -> dict:
    """
    Scrape Spotify playlist and return data (no storage)
    """
    
    async with async_playwright() as p:
        print("正在啟動瀏覽器...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        print(f"正在載入歌單: {playlist_url}")
        await page.goto(playlist_url)
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)
        
        # Get playlist name
        playlist_name = "Spotify Playlist"
        try:
            elem = await page.query_selector('h1[data-testid="entityTitle"]')
            if elem:
                playlist_name = await elem.inner_text()
            else:
                title = await page.title()
                playlist_name = title.split(' - playlist by')[0] if ' - playlist by' in title else "Spotify Playlist"
        except:
            pass
        
        print(f"歌單名稱: {playlist_name}")
        print("正在使用鍵盤導航收集歌曲...")
        
        # Click on the tracklist to focus it
        try:
            tracklist = await page.query_selector('[data-testid="playlist-tracklist"]')
            if tracklist:
                await tracklist.click()
                await asyncio.sleep(0.5)
        except:
            pass
        
        # Press Home to go to top
        await page.keyboard.press('Home')
        await asyncio.sleep(1)
        
        # Collect tracks by pressing PageDown repeatedly
        collected = {}
        no_new_count = 0
        max_no_new = 30
        
        while no_new_count < max_no_new:
            # Get current visible tracks
            rows = await page.query_selector_all('[data-testid="tracklist-row"]')
            
            for row in rows:
                try:
                    # Get track name
                    title_elem = await row.query_selector('[data-testid="internal-track-link"]')
                    if not title_elem:
                        continue
                    title = await title_elem.inner_text()
                    title = title.strip()
                    
                    # Get artists
                    artist_elems = await row.query_selector_all('a[href*="/artist/"]')
                    artists = []
                    for ae in artist_elems:
                        name = await ae.inner_text()
                        if name and name.strip():
                            artists.append(name.strip())
                    
                    key = f"{title}|||{'|||'.join(artists)}"
                    if key not in collected:
                        collected[key] = {
                            'title': title,
                            'artists': artists
                        }
                        print(f"  [{len(collected)}] {title} - {', '.join(artists)}")
                        no_new_count = 0
                except:
                    continue
            
            # Scroll down using keyboard
            await page.keyboard.press('PageDown')
            await asyncio.sleep(0.3)
            no_new_count += 1
        
        await browser.close()
    
    # Format tracks
    tracks = []
    for i, (key, data) in enumerate(collected.items()):
        tracks.append({
            'index': i + 1,
            'name': data['title'],
            'artists': data['artists'],
            'search_query': f"{data['title']} {' '.join(data['artists'])}"
        })
    
    result = {
        'playlist_name': playlist_name,
        'playlist_url': playlist_url,
        'total_tracks': len(tracks),
        'tracks': tracks
    }
    
    print(f"\n完成！共抓取 {len(tracks)} 首歌曲")
    return result


if __name__ == '__main__':
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://open.spotify.com/playlist/7Efaw5INyn3zbHlarlNH2Q"
    result = asyncio.run(scrape_playlist_to_memory(url))
    print(f"歌單: {result['playlist_name']}")
    print(f"歌曲數: {result['total_tracks']}")
