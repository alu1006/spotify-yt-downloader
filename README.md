# 🎵 Spotify to YouTube Converter

將 Spotify 歌單轉換成 YouTube 歌單，並可下載為 MP3！

![Demo](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ 功能

- 📋 **抓取 Spotify 歌單** - 自動從 Spotify 公開歌單抓取所有歌曲資訊
- 📺 **建立 YouTube 歌單** - 將抓取的歌曲建立成 YouTube 播放清單
- 📥 **下載 MP3** - 使用 yt-dlp 下載所有歌曲為 MP3 格式
- 🌐 **網頁介面** - 美觀易用的 Web UI

## 🚀 快速開始

### 1. 安裝相依套件

```bash
# 建立虛擬環境（建議）
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# 安裝 Python 套件
pip install -r requirements.txt

# 安裝 Playwright 瀏覽器
playwright install chromium

# 安裝 yt-dlp（用於下載 MP3）
brew install yt-dlp  # macOS
# 或 pip install yt-dlp
```

### 2. 啟動網頁應用程式

```bash
python web_app.py
```

然後開啟瀏覽器前往 http://127.0.0.1:5000

### 3. 使用方式

1. **輸入 Spotify 歌單網址** - 貼上公開的 Spotify 歌單連結
2. **點擊「抓取歌單」** - 等待抓取完成
3. **下載 MP3** 或 **建立 YouTube 歌單**

## 📁 專案結構

```
spotify_yt_downloader/
├── web_app.py           # Flask 網頁應用程式
├── scraper_memory.py    # Spotify 歌單抓取器
├── youtube_playlist.py  # YouTube API 整合
├── templates/
│   └── index.html       # 網頁前端
├── downloads/           # MP3 下載資料夾
└── requirements.txt     # Python 相依套件
```

## ⚙️ 建立 YouTube 歌單（可選）

如果要使用「建立 YouTube 歌單」功能，需要設定 Google API：

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 建立新專案
3. 啟用 YouTube Data API v3
4. 建立 OAuth 2.0 憑證
5. 下載 `client_secret.json` 並放在專案根目錄

## 📝 注意事項

- 只支援**公開的 Spotify 歌單**（私人歌單需要登入）
- 下載功能需要安裝 `yt-dlp`
- YouTube 歌單功能需要 Google API 憑證

## 🛠️ 技術棧

- **後端**: Python, Flask
- **前端**: HTML, CSS, JavaScript
- **爬蟲**: Playwright
- **下載**: yt-dlp
- **API**: YouTube Data API v3

## 📄 License

MIT License
