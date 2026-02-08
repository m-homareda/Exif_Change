import piexif
from PIL import Image
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import shutil
from datetime import datetime
from tkcalendar import DateEntry  # 追加: カレンダーウィジェット

# --- EXIF操作用関数 (変更なし) ---

def get_current_exif(file_path):
    """
    画像の現在のEXIF情報を読み取り、テキストとして返す
    """
    artist = ""
    date_str = ""
    
    try:
        img = Image.open(file_path)
        if 'exif' in img.info:
            exif_dict = piexif.load(img.info['exif'])
            
            # 撮影者 (Artist)
            if piexif.ImageIFD.Artist in exif_dict['0th']:
                try:
                    artist = exif_dict['0th'][piexif.ImageIFD.Artist].decode('utf-8').rstrip('\x00')
                except:
                    pass

            # 撮影日時 (DateTimeOriginal)
            if piexif.ExifIFD.DateTimeOriginal in exif_dict['Exif']:
                try:
                    date_str = exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal].decode('utf-8')
                except:
                    pass
    except Exception:
        pass

    # 日付が取得できなかった場合は現在時刻を入れる
    if not date_str:
        date_str = datetime.now().strftime("%Y:%m:%d %H:%M:%S")

    return artist, date_str

def save_new_exif_smart(input_path, output_path, new_artist, new_datetime):
    """
    拡張子に応じて最適な保存方法（無劣化）を選択する関数
    """
    try:
        # 1. 元画像からEXIF辞書データのベースを作成
        img = Image.open(input_path)
        if 'exif' in img.info:
            exif_dict = piexif.load(img.info['exif'])
        else:
            exif_dict = {"0th":{}, "Exif":{}, "GPS":{}, "1st":{}, "thumbnail":None}
        
        # 2. 辞書データを更新
        exif_dict['0th'][piexif.ImageIFD.Artist] = new_artist.encode('utf-8')
        exif_dict['0th'][piexif.ImageIFD.Software] = "Python Exif Editor".encode('utf-8')
        
        exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = new_datetime.encode('utf-8')
        exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = new_datetime.encode('utf-8')
        exif_dict['0th'][piexif.ImageIFD.DateTime] = new_datetime.encode('utf-8')

        # 3. バイト列を作成
        exif_bytes = piexif.dump(exif_dict)

        # --- 分岐処理 ---
        base_name, ext = os.path.splitext(output_path)
        ext = ext.lower()

        if ext in ['.jpg', '.jpeg']:
            img.close() 
            if os.path.abspath(input_path) != os.path.abspath(output_path):
                shutil.copy2(input_path, output_path)
            piexif.insert(exif_bytes, output_path)
            return True, "保存成功（JPEG注入モード）"

        else:
            img.save(output_path, exif=exif_bytes)
            return True, f"保存成功（{ext.upper()}保存モード）"

    except Exception as e:
        return False, str(e)

# --- GUI用関数 (大幅変更) ---

def open_editor():
    root = tk.Tk()
    root.withdraw()
    
    input_path = filedialog.askopenfilename(
        title="編集する画像を選択",
        filetypes=[
            ("画像ファイル", "*.jpg;*.jpeg;*.png;*.webp"),
            ("すべてのファイル", "*.*")
        ]
    )
    
    if not input_path:
        root.destroy()
        return

    # EXIFから現在の情報を取得
    current_artist, current_date_str = get_current_exif(input_path)
    
    # 日付文字列をdatetimeオブジェクトに変換 (初期値セット用)
    try:
        # EXIFの日付形式は "YYYY:MM:DD HH:MM:SS"
        dt_obj = datetime.strptime(current_date_str, "%Y:%m:%d %H:%M:%S")
    except ValueError:
        dt_obj = datetime.now()

    editor = tk.Toplevel(root)
    editor.title("EXIF情報編集")
    editor.geometry("450x300") # 少し横長に
    
    def on_close():
        root.destroy()
    editor.protocol("WM_DELETE_WINDOW", on_close)

    frame = ttk.Frame(editor, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)

    # --- ファイル名表示 ---
    lbl_file = ttk.Label(frame, text=f"対象: {os.path.basename(input_path)}", font=("Meiryo", 10, "bold"))
    lbl_file.pack(pady=(0, 20))

    # --- 撮影者入力 ---
    ttk.Label(frame, text="撮影者 (Artist):").pack(anchor=tk.W)
    entry_artist = ttk.Entry(frame, width=40)
    entry_artist.insert(0, current_artist)
    entry_artist.pack(pady=(0, 15))

    # --- 日時入力エリア (フレームでまとめる) ---
    ttk.Label(frame, text="撮影日時:").pack(anchor=tk.W)
    
    date_frame = ttk.Frame(frame)
    date_frame.pack(anchor=tk.W, pady=(0, 20))

    # 1. カレンダー (日付)
    # locale='ja_JP' で日本語化 (OSの設定に依存します)
    # weekendbackground: 週末の背景色
    # weekendforeground: 週末の文字色
    # headersbackground: 曜日部分の背景色
    cal = DateEntry(date_frame, width=12, background='darkblue',
                    foreground='white', borderwidth=2, 
                    date_pattern='yyyy/mm/dd',
                    locale='ja_JP',              # 日本語化 (月・火・水...)
                    weekendbackground='#ffc0cb', # 週末の背景を「薄いピンク」に
                    weekendforeground='black',   # 週末の文字を「黒」に
                    headersbackground='#333',    # 曜日バーを「濃いグレー」に
                    headersforeground='white',    # 曜日バーの文字を「白」に
                    showweeknumbers=False
                    )
    cal.set_date(dt_obj) # 元の日付をセット
    cal.pack(side=tk.LEFT, padx=(0, 10))

    # 2. 時間 (時:分:秒) -> Spinboxを使う
    
    # 時 (0-23)
    spin_hour = ttk.Spinbox(date_frame, from_=0, to=23, width=3, format="%02.0f", wrap=True)
    spin_hour.set(dt_obj.hour)
    spin_hour.pack(side=tk.LEFT)
    ttk.Label(date_frame, text=":").pack(side=tk.LEFT)

    # 分 (0-59)
    spin_minute = ttk.Spinbox(date_frame, from_=0, to=59, width=3, format="%02.0f", wrap=True)
    spin_minute.set(dt_obj.minute)
    spin_minute.pack(side=tk.LEFT)
    ttk.Label(date_frame, text=":").pack(side=tk.LEFT)

    # 秒 (0-59)
    spin_second = ttk.Spinbox(date_frame, from_=0, to=59, width=3, format="%02.0f", wrap=True)
    spin_second.set(dt_obj.second)
    spin_second.pack(side=tk.LEFT)

    # --- 保存ボタンの処理 ---
    def on_save_click():
        new_artist = entry_artist.get()
        
        selected_date = cal.get_date()
        h = int(spin_hour.get())
        m = int(spin_minute.get())
        s = int(spin_second.get())
        
        new_date_str = f"{selected_date.year:04d}:{selected_date.month:02d}:{selected_date.day:02d} {h:02d}:{m:02d}:{s:02d}"

        dir_name, file_name = os.path.split(input_path)
        base_name, ext = os.path.splitext(file_name)
        default_output = f"{base_name}_edited{ext}"

        output_path = filedialog.asksaveasfilename(
            title="保存先を指定",
            initialdir=dir_name,
            initialfile=default_output,
            defaultextension=ext,
            filetypes=[("元の形式", f"*{ext}")]
        )

        if output_path:
            success, msg = save_new_exif_smart(input_path, output_path, new_artist, new_date_str)
            
            if success:
                # --- 追加機能: 書き込まれたデータを検証する ---
                verified_artist, verified_date = get_current_exif(output_path)
                
                # 検証メッセージを作成
                verify_msg = f"保存と検証が完了しました！\n\n【保存されたデータ】\n日時: {verified_date}\n撮影者: {verified_artist}\n\n保存先:\n{output_path}"
                
                if verified_date == new_date_str:
                    messagebox.showinfo("成功 (検証OK)", verify_msg)
                    root.destroy()
                else:
                    # 万が一書き換わっていない場合
                    messagebox.showwarning("警告", f"保存処理は完了しましたが、検証で値の不一致が確認されました。\n\n期待値: {new_date_str}\n実測値: {verified_date}\n\nWindowsの仕様やPNGの形式により、EXIFが保持されていない可能性があります。")
            else:
                messagebox.showerror("エラー", f"失敗しました:\n{msg}")
                
    btn_save = ttk.Button(frame, text="保存先を選んで実行", command=on_save_click)
    btn_save.pack(fill=tk.X, pady=10)

    root.mainloop()

if __name__ == "__main__":
    open_editor()