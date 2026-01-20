#!/usr/bin/env python3
"""
Spotify to YouTube Converter - GUI Application (Fixed Version)
圖形化介面：Spotify 歌單轉換 YouTube 歌單並下載
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import os
import subprocess
from pathlib import Path
from database import get_current_playlist


class SpotifyYouTubeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Spotify to YouTube 歌單轉換器")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # Configure style
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Helvetica', 16, 'bold'))
        style.configure('Header.TLabel', font=('Helvetica', 12, 'bold'))
        
        self.create_widgets()
        self.tracks = []
        
        # Setup clipboard bindings after widgets are created
        self.setup_clipboard_bindings()
    
    def setup_clipboard_bindings(self):
        """Setup macOS clipboard shortcuts for all Entry widgets"""
        # Bind to both Command and Control for compatibility
        for widget in [self.url_entry, self.playlist_name_entry]:
            widget.bind('<Command-v>', lambda e: self.do_paste(e))
            widget.bind('<Control-v>', lambda e: self.do_paste(e))
            widget.bind('<Command-c>', lambda e: self.do_copy(e))
            widget.bind('<Control-c>', lambda e: self.do_copy(e))
            widget.bind('<Command-a>', lambda e: self.do_select_all(e))
            widget.bind('<Control-a>', lambda e: self.do_select_all(e))
            widget.bind('<Command-x>', lambda e: self.do_cut(e))
            widget.bind('<Control-x>', lambda e: self.do_cut(e))
            # Also add right-click menu
            widget.bind('<Button-2>', lambda e: self.show_context_menu(e))
            widget.bind('<Control-Button-1>', lambda e: self.show_context_menu(e))
    
    def do_paste(self, event):
        try:
            widget = event.widget
            try:
                widget.delete('sel.first', 'sel.last')
            except:
                pass
            widget.insert('insert', self.root.clipboard_get())
        except Exception as e:
            print(f"Paste error: {e}")
        return 'break'
    
    def do_copy(self, event):
        try:
            widget = event.widget
            text = widget.selection_get()
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
        except:
            pass
        return 'break'
    
    def do_cut(self, event):
        try:
            widget = event.widget
            text = widget.selection_get()
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            widget.delete('sel.first', 'sel.last')
        except:
            pass
        return 'break'
    
    def do_select_all(self, event):
        event.widget.select_range(0, 'end')
        event.widget.icursor('end')
        return 'break'
    
    def show_context_menu(self, event):
        """Show right-click context menu"""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="剪下", command=lambda: self.do_cut_menu(event.widget))
        menu.add_command(label="複製", command=lambda: self.do_copy_menu(event.widget))
        menu.add_command(label="貼上", command=lambda: self.do_paste_menu(event.widget))
        menu.add_separator()
        menu.add_command(label="全選", command=lambda: event.widget.select_range(0, 'end'))
        menu.tk_popup(event.x_root, event.y_root)
    
    def do_paste_menu(self, widget):
        try:
            try:
                widget.delete('sel.first', 'sel.last')
            except:
                pass
            widget.insert('insert', self.root.clipboard_get())
        except:
            pass
    
    def do_copy_menu(self, widget):
        try:
            text = widget.selection_get()
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
        except:
            pass
    
    def do_cut_menu(self, widget):
        try:
            text = widget.selection_get()
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            widget.delete('sel.first', 'sel.last')
        except:
            pass
        
    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="🎵 Spotify to YouTube 歌單轉換器", style='Title.TLabel')
        title_label.pack(pady=(0, 15))
        
        # === Section 1: Spotify URL Input ===
        url_frame = ttk.LabelFrame(main_frame, text="步驟 1: Spotify 歌單", padding="10")
        url_frame.pack(fill=tk.X, pady=5)
        
        url_row = ttk.Frame(url_frame)
        url_row.pack(fill=tk.X)
        
        ttk.Label(url_row, text="網址:").pack(side=tk.LEFT)
        self.url_var = tk.StringVar(value="https://open.spotify.com/playlist/")
        self.url_entry = ttk.Entry(url_row, textvariable=self.url_var, width=55)
        self.url_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.scrape_btn = ttk.Button(url_row, text="🌐 開啟抓取工具", command=self.start_scrape)
        self.scrape_btn.pack(side=tk.RIGHT, padx=2)
        
        self.load_btn = ttk.Button(url_row, text="📂 載入現有資料", command=self.load_existing_tracks)
        self.load_btn.pack(side=tk.RIGHT, padx=2)
        
        # === Section 2: Track List ===
        tracks_frame = ttk.LabelFrame(main_frame, text="步驟 2: 歌曲清單", padding="10")
        tracks_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        columns = ('index', 'name', 'artists')
        self.tracks_tree = ttk.Treeview(tracks_frame, columns=columns, show='headings', height=10)
        self.tracks_tree.heading('index', text='#')
        self.tracks_tree.heading('name', text='歌曲名稱')
        self.tracks_tree.heading('artists', text='藝人')
        self.tracks_tree.column('index', width=40, anchor='center')
        self.tracks_tree.column('name', width=300)
        self.tracks_tree.column('artists', width=250)
        
        scrollbar = ttk.Scrollbar(tracks_frame, orient=tk.VERTICAL, command=self.tracks_tree.yview)
        self.tracks_tree.configure(yscrollcommand=scrollbar.set)
        
        self.tracks_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.track_count_var = tk.StringVar(value="歌曲數量: 0")
        ttk.Label(main_frame, textvariable=self.track_count_var).pack(anchor=tk.W)
        
        # === Section 3: Actions ===
        action_frame = ttk.LabelFrame(main_frame, text="步驟 3: 執行操作", padding="10")
        action_frame.pack(fill=tk.X, pady=5)
        
        yt_name_frame = ttk.Frame(action_frame)
        yt_name_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(yt_name_frame, text="YouTube 歌單名稱:").pack(side=tk.LEFT)
        self.playlist_name_var = tk.StringVar(value="My Playlist")
        self.playlist_name_entry = ttk.Entry(yt_name_frame, textvariable=self.playlist_name_var, width=40)
        self.playlist_name_entry.pack(side=tk.LEFT, padx=10)
        
        btn_frame = ttk.Frame(action_frame)
        btn_frame.pack(fill=tk.X)
        
        self.create_yt_btn = ttk.Button(btn_frame, text="📋 建立 YouTube 歌單", command=self.start_create_playlist)
        self.create_yt_btn.pack(side=tk.LEFT, padx=5)
        
        self.download_btn = ttk.Button(btn_frame, text="📥 下載全部歌曲 (MP3)", command=self.start_download)
        self.download_btn.pack(side=tk.LEFT, padx=5)
        
        self.open_folder_btn = ttk.Button(btn_frame, text="📁 開啟下載資料夾", command=self.open_download_folder)
        self.open_folder_btn.pack(side=tk.LEFT, padx=5)
        
        # === Section 4: Log Output ===
        log_frame = ttk.LabelFrame(main_frame, text="執行記錄", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.status_var = tk.StringVar(value="就緒")
        ttk.Label(main_frame, textvariable=self.status_var).pack(anchor=tk.W)
        
    def log(self, message):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
        self.root.update_idletasks()
        
    def clear_log(self):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)
        
    def start_scrape(self):
        """Start scraping in a separate process"""
        url = self.url_var.get().strip()
        if not url or 'spotify.com/playlist/' not in url:
            messagebox.showerror("錯誤", "請輸入有效的 Spotify 歌單網址")
            return
        
        self.clear_log()
        self.log("正在自動抓取歌單...")
        self.log("請稍候，這可能需要 1-2 分鐘")
        self.scrape_btn.configure(state=tk.DISABLED)
        self.status_var.set("正在抓取中...")
        
        threading.Thread(target=self.run_scraper_process, args=(url,), daemon=True).start()
        
    def run_scraper_process(self, url):
        """Run auto scraper as subprocess"""
        try:
            result = subprocess.run(
                ['python', 'auto_scraper.py', url],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__)),
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                self.root.after(0, self.load_existing_tracks)
                self.root.after(0, lambda: self.log("\n✓ 抓取完成！"))
            else:
                self.root.after(0, lambda: self.log(f"錯誤:\n{result.stderr}"))
                
        except subprocess.TimeoutExpired:
            self.root.after(0, lambda: self.log("錯誤: 抓取逾時"))
        except Exception as e:
            self.root.after(0, lambda: self.log(f"錯誤: {e}"))
        finally:
            self.root.after(0, lambda: self.scrape_btn.configure(state=tk.NORMAL))
            self.root.after(0, lambda: self.status_var.set("就緒"))
            
    def load_existing_tracks(self):
        """Load tracks from database"""
        try:
            data = get_current_playlist()
            self.tracks = data['tracks']
            
            if self.tracks:
                self.playlist_name_var.set(data.get('playlist_name', 'My Playlist'))
                self.update_tracks_list()
                self.log(f"已載入: {len(self.tracks)} 首歌曲")
            else:
                messagebox.showinfo("提示", "找不到現有資料，請先抓取歌單")
        except Exception as e:
            messagebox.showerror("錯誤", f"載入失敗: {e}")
                
    def update_tracks_list(self):
        for item in self.tracks_tree.get_children():
            self.tracks_tree.delete(item)
        
        for track in self.tracks:
            artists = ', '.join(track.get('artists', []))
            self.tracks_tree.insert('', tk.END, values=(
                track['index'],
                track['name'],
                artists
            ))
        
        self.track_count_var.set(f"歌曲數量: {len(self.tracks)}")
        
    def start_create_playlist(self):
        if not self.tracks:
            self.load_existing_tracks()
            if not self.tracks:
                messagebox.showerror("錯誤", "請先抓取或載入歌單")
                return
        
        playlist_name = self.playlist_name_var.get().strip()
        if not playlist_name:
            messagebox.showerror("錯誤", "請輸入歌單名稱")
            return
            
        self.create_yt_btn.configure(state=tk.DISABLED)
        self.status_var.set("正在建立 YouTube 歌單...")
        self.clear_log()
        threading.Thread(target=self.create_youtube_playlist, args=(playlist_name,), daemon=True).start()
        
    def create_youtube_playlist(self, playlist_name):
        try:
            from youtube_playlist import create_youtube_playlist_from_tracks
            
            self.root.after(0, lambda: self.log(f"正在建立歌單: {playlist_name}"))
            self.root.after(0, lambda: self.log(f"共 {len(self.tracks)} 首歌曲\n"))
            
            results = create_youtube_playlist_from_tracks(self.tracks, playlist_name)
            
            self.root.after(0, lambda: self.log(f"\n完成！"))
            self.root.after(0, lambda: self.log(f"成功: {len(results['added'])} 首"))
            self.root.after(0, lambda: self.log(f"失敗: {len(results['not_found'])} 首"))
            self.root.after(0, lambda: self.log(f"\n歌單網址:\n{results['playlist_url']}"))
            
            self.root.after(0, lambda: messagebox.showinfo("完成", f"歌單已建立！\n{results['playlist_url']}"))
            
        except Exception as e:
            self.root.after(0, lambda: self.log(f"錯誤: {e}"))
            self.root.after(0, lambda: messagebox.showerror("錯誤", str(e)))
        finally:
            self.root.after(0, lambda: self.create_yt_btn.configure(state=tk.NORMAL))
            self.root.after(0, lambda: self.status_var.set("就緒"))
            
    def start_download(self):
        if not self.tracks:
            self.load_existing_tracks()
            if not self.tracks:
                messagebox.showerror("錯誤", "請先抓取或載入歌單")
                return
        
        self.download_btn.configure(state=tk.DISABLED)
        self.status_var.set("正在下載歌曲...")
        self.clear_log()
        threading.Thread(target=self.download_songs, daemon=True).start()
        
    def download_songs(self):
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            download_dir = Path(os.path.join(base_dir, 'downloads'))
            download_dir.mkdir(exist_ok=True)
            
            total = len(self.tracks)
            success = 0
            
            for i, track in enumerate(self.tracks):
                artists = ', '.join(track.get('artists', []))
                search_query = track.get('search_query', f"{track['name']} {artists}")
                
                filename = f"{track['name']} - {artists}"
                filename = "".join(c for c in filename if c not in r'\/:*?"<>|')
                
                self.root.after(0, lambda t=track, idx=i: self.log(f"[{idx+1}/{total}] {t['name']}"))
                self.root.after(0, lambda p=(i+1)/total*100: self.progress_var.set(p))
                
                try:
                    cmd = [
                        'yt-dlp', '-x', '--audio-format', 'mp3',
                        '--audio-quality', '0',
                        '-o', str(download_dir / f'{filename}.%(ext)s'),
                        '--no-playlist', '--quiet',
                        '--default-search', 'ytsearch',
                        f'ytsearch:{search_query}'
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                    
                    if result.returncode == 0:
                        success += 1
                        
                except Exception as e:
                    pass
            
            self.root.after(0, lambda: self.log(f"\n下載完成！成功: {success}/{total}"))
            self.root.after(0, lambda: self.progress_var.set(100))
            self.root.after(0, lambda: messagebox.showinfo("完成", f"下載完成！\n成功: {success}/{total}"))
            
        except Exception as e:
            self.root.after(0, lambda: self.log(f"錯誤: {e}"))
            self.root.after(0, lambda: messagebox.showerror("錯誤", str(e)))
        finally:
            self.root.after(0, lambda: self.download_btn.configure(state=tk.NORMAL))
            self.root.after(0, lambda: self.status_var.set("就緒"))
            
    def open_download_folder(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        download_dir = Path(os.path.join(base_dir, 'downloads'))
        download_dir.mkdir(exist_ok=True)
        subprocess.run(['open', download_dir])


def main():
    root = tk.Tk()
    app = SpotifyYouTubeGUI(root)
    
    # Auto-load existing tracks from database
    try:
        data = get_current_playlist()
        if data['tracks']:
            app.load_existing_tracks()
    except:
        pass
    
    root.mainloop()


if __name__ == '__main__':
    main()
