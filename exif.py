import piexif
from PIL import Image
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import shutil  # ファイルコピー用
from datetime import datetime

# --- EXIF操作用関数 ---

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

    if not date_str:
        date_str = datetime.now().strftime("%Y:%m:%d %H:%M:%S")

    return artist, date_str

def save_new_exif_lossless(input_path, output_path, new_artist, new_datetime):
    """
    【重要】画像の再圧縮を行わず、EXIFデータだけを差し替える関数
    """
    try:
        # 1. まず元のファイルをそのままコピーする（画質劣化を防ぐため）
        # 入力と出力が同じパスの場合はコピー不要
        if os.path.abspath(input_path) != os.path.abspath(output_path):
            shutil.copy2(input_path, output_path)

        # 2. コピー先のファイルからEXIF情報を読み込む（なければ作成）
        # piexifはファイルパスから直接読めないので、一旦Pillowでヘッダーだけ読む
        img = Image.open(output_path)
        if 'exif' in img.info:
            exif_dict = piexif.load(img.info['exif'])
        else:
            exif_dict = {"0th":{}, "Exif":{}, "GPS":{}, "1st":{}, "thumbnail":None}
        img.close() # ファイルを閉じる

        # 3. 辞書データを更新
        exif_dict['0th'][piexif.ImageIFD.Artist] = new_artist.encode('utf-8')
        exif_dict['0th'][piexif.ImageIFD.Software] = "Python Lossless Editor".encode('utf-8')
        
        exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = new_datetime.encode('utf-8')
        exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = new_datetime.encode('utf-8')
        exif_dict['0th'][piexif.ImageIFD.DateTime] = new_datetime.encode('utf-8')

        # 4. バイト列を作成
        exif_bytes = piexif.dump(exif_dict)

        # 5. insertを使って、画像データに触れずにEXIFだけ注入する
        piexif.insert(exif_bytes, output_path)
        
        return True, "保存成功（無劣化）"

    except Exception as e:
        # エラーが起きたら、作りかけの出力ファイルを消すなどの処理を入れても良い
        return False, str(e)

# --- GUI用関数 ---

def open_editor():
    root = tk.Tk()
    root.withdraw()
    
    input_path = filedialog.askopenfilename(
        title="編集する画像を選択",
        filetypes=[("JPEG画像", "*.jpg;*.jpeg")]
    )
    
    if not input_path:
        root.destroy()
        return

    current_artist, current_date = get_current_exif(input_path)

    editor = tk.Toplevel(root)
    editor.title("EXIF情報入力（無劣化モード）")
    editor.geometry("400x250")
    
    def on_close():
        root.destroy()
    editor.protocol("WM_DELETE_WINDOW", on_close)

    frame = ttk.Frame(editor, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)

    lbl_file = ttk.Label(frame, text=f"対象: {os.path.basename(input_path)}")
    lbl_file.pack(pady=(0, 15))

    ttk.Label(frame, text="撮影者 (Artist):").pack(anchor=tk.W)
    entry_artist = ttk.Entry(frame, width=40)
    entry_artist.insert(0, current_artist)
    entry_artist.pack(pady=(0, 10))

    ttk.Label(frame, text="撮影日時 (YYYY:MM:DD HH:MM:SS):").pack(anchor=tk.W)
    entry_date = ttk.Entry(frame, width=40)
    entry_date.insert(0, current_date)
    entry_date.pack(pady=(0, 20))

    def on_save_click():
        new_artist = entry_artist.get()
        new_date = entry_date.get()

        dir_name, file_name = os.path.split(input_path)
        base_name, ext = os.path.splitext(file_name)
        default_output = f"{base_name}_edited{ext}"

        output_path = filedialog.asksaveasfilename(
            title="保存先を指定",
            initialdir=dir_name,
            initialfile=default_output,
            defaultextension=".jpg",
            filetypes=[("JPEG画像", "*.jpg;*.jpeg")]
        )

        if output_path:
            # ここで新しい無劣化関数を呼ぶ
            success, msg = save_new_exif_lossless(input_path, output_path, new_artist, new_date)
            if success:
                messagebox.showinfo("完了", f"保存しました！\n（画質劣化なし）\n{output_path}")
                root.destroy()
            else:
                messagebox.showerror("エラー", f"失敗しました:\n{msg}")

    btn_save = ttk.Button(frame, text="保存先を選んで実行", command=on_save_click)
    btn_save.pack(fill=tk.X)

    root.mainloop()

if __name__ == "__main__":
    open_editor()