# Exif Change

画像の画質を劣化させずに、撮影者名や撮影日時などのEXIF情報を書き換えるPythonツールです。

一眼レフなどで撮影した写真の整理や、SNSアップロード前のプライバシー保護・情報修正に役立ちます。

## 機能
- スマート保存: JPEGファイルは画質劣化なし（無劣化）でEXIF情報のみを書き換えます。PNGやWebP形式の編集にも対応しています。
- カレンダーUI: カレンダーを使って直感的に日付を選択・入力できます。
- 編集項目:
    - Artist（撮影者）
    - DateTimeOriginal（撮影日時）

## 使用技術
- Python
- Pillow (PIL)
- piexif
- tkcalendar
- Tkinter