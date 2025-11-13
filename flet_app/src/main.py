import flet as ft
from postarization import postarization
from PIL import Image, ImageFile
import base64
from io import BytesIO
import threading
import os
import gc
import time
import urllib.parse
import traceback

# 切り詰められた画像ファイルを読み込めるようにする
ImageFile.LOAD_TRUNCATED_IMAGES = True

# メモリ節約のための最大画像サイズ（幅または高さ）
MAX_IMAGE_SIZE = 1280

# 例として同ファイル内に定義しておきます
PARAMETER_SETS = {
    "default":    {"saturation": 2,   "level": 8,  "smooth_strength": 50, "edge_strength": 0.4},
    "realistic":  {"saturation": 1.5, "level": 12, "smooth_strength": 70, "edge_strength": 0.3},
    "anime_style":{"saturation": 2.5, "level": 6,  "smooth_strength": 40, "edge_strength": 0.5},
    "monochrome": {"saturation": 0, "level": 4,  "smooth_strength": 80, "edge_strength": 0.2},
    "novel_game": {"saturation": 1.6, "level": 8, "smooth_strength": 68, "edge_strength": 0.8},
}

def cleanup_old_files(directory: str, max_age_seconds: int = 3600):
    """指定時間より古いファイルを削除"""
    try:
        if not os.path.exists(directory):
            return
        
        current_time = time.time()
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > max_age_seconds:
                    os.remove(file_path)
                    print(f"[INFO] Cleaned up old file: {filename}")
    except Exception as e:
        print(f"[WARNING] Cleanup failed: {e}")

def resize_image_if_needed(img: Image.Image, max_size: int = MAX_IMAGE_SIZE) -> Image.Image:
    """画像が大きすぎる場合はリサイズする"""
    width, height = img.size
    if width <= max_size and height <= max_size:
        return img
    
    # アスペクト比を維持してリサイズ
    if width > height:
        new_width = max_size
        new_height = int(height * (max_size / width))
    else:
        new_height = max_size
        new_width = int(width * (max_size / height))
    
    print(f"[INFO] Resizing image from {width}x{height} to {new_width}x{new_height}")
    return img.resize((new_width, new_height), Image.Resampling.LANCZOS)


def main(page: ft.Page):
    # page.window_maximized = True
    # page.window_full_screen = True
    page.title = "Postarization Filter"
    page.scroll = "auto"

    # Web版の場合、起動時に古いファイルをクリーンアップ
    if page.web:
        upload_dir = os.getenv("FLET_UPLOAD_DIR", os.path.join(os.getcwd(), "storage", "temp"))
        cleanup_old_files(upload_dir, max_age_seconds=3600)  # 1時間以上古いファイルを削除

    original_image = None
    current_image = None
    update_timer = None  # デバウンス用のタイマー

    # ローディング（プログレスリング）
    loading_indicator = ft.ProgressRing(visible=False, width=50, height=50, color=ft.Colors.BLUE)

    # 画像プレビュー用コントロール
    image_control = ft.Image(width=1400, fit=ft.ImageFit.CONTAIN)

    # Stack でプレビュー画像とローディングを重ねる
    image_stack = ft.Stack(
        controls=[
            image_control,
            ft.Container(content=loading_indicator, alignment=ft.alignment.center)
        ]
    )

    # スライダー（初期は無効） + 値表示
    slider_satur = ft.Slider(min=0.0, max=3.0, value=2.0, divisions=30, disabled=True)
    slider_level = ft.Slider(min=2, max=20, value=8, divisions=18, disabled=True)
    slider_smooth = ft.Slider(min=0, max=200, value=50, divisions=200, disabled=True)
    slider_edge = ft.Slider(min=0.0, max=2.0, value=0.4, divisions=200, disabled=True)

    satur_value_text = ft.Text(value=f"{slider_satur.value:.2f}", width=50)
    level_value_text = ft.Text(value=f"{int(slider_level.value)}", width=50)
    smooth_value_text = ft.Text(value=f"{slider_smooth.value}", width=50)
    edge_value_text = ft.Text(value=f"{slider_edge.value:.2f}", width=50)

    # スライダー値をBase64エンコード用に画像変換する関数
    def pil_to_base64(img: Image.Image, fmt="JPEG") -> str:
        buf = BytesIO()
        img.save(buf, format=fmt)
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    # エクスポート用の処理
    def on_save_dialog_result(e: ft.FilePickerResultEvent):
        print(f"[DEBUG] on_save_dialog_result called")
        if not e.path:
            print(f"[DEBUG] Save dialog cancelled")
            return
        if not current_image:
            print(f"[ERROR] No image to save")
            return
        try:
            save_path = e.path
            print(f"[DEBUG] Original path: {save_path}")
            print(f"[DEBUG] Path type: {type(save_path)}")
            
            # 拡張子がない場合は.pngを追加
            if not save_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                save_path += '.png'
            
            print(f"[DEBUG] Final save path: {save_path}")
            
            # 拡張子から形式を判定
            if save_path.lower().endswith('.png'):
                img_format = 'PNG'
            elif save_path.lower().endswith(('.jpg', '.jpeg')):
                img_format = 'JPEG'
            else:
                img_format = 'PNG'
            
            print(f"[DEBUG] Saving as format: {img_format}")
            current_image.save(save_path, format=img_format)
            print(f"[SUCCESS] Image saved successfully to {save_path}")
        except Exception as ex:
            print(f"[ERROR] 画像の保存に失敗しました: {ex}")
            traceback.print_exc()

    def on_export_click(e):
        print(f"[DEBUG] on_export_click called")
        if not current_image:
            print(f"[ERROR] No image to export")
            return
        
        try:
            # デスクトップ版: ファイル保存ダイアログを使用
            if not page.web:
                print(f"[DEBUG] Using file save dialog for desktop")
                file_picker_save.save_file(
                    dialog_title="Save Filtered Image",
                    file_name="filtered_image.png",
                    allowed_extensions=["png", "jpg", "jpeg"]
                )
            else:
                # Web版: base64エンコードして直接ダウンロード
                print(f"[DEBUG] Creating base64 download for web")
                
                timestamp = int(time.time())
                filename = f"filtered_image_{timestamp}.png"
                
                # 画像をbase64エンコード
                buf = BytesIO()
                current_image.save(buf, format="PNG")
                buf.seek(0)
                b64_data = base64.b64encode(buf.getvalue()).decode()
                
                # ダウンロード用のHTMLページを作成
                download_html = f"""<!DOCTYPE html>
                <html>
                <head><title>Download</title></head>
                <body>
                <p>Downloading...</p>
                <script>
                window.onload = function() {{
                    const link = document.createElement('a');
                    link.download = '{filename}';
                    link.href = 'data:image/png;base64,{b64_data}';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    setTimeout(function() {{ window.close(); }}, 100);
                }};
                </script>
                </body>
                </html>
                """
                
                # HTMLページを新しいウィンドウで開く
                page.launch_url(f"data:text/html;charset=utf-8,{urllib.parse.quote(download_html)}", web_window_name="_blank")
                print(f"[DEBUG] Download initiated: {filename}")

        except Exception as ex:
            print(f"[ERROR] エクスポートに失敗しました: {ex}")
            traceback.print_exc()

    export_button = ft.ElevatedButton(
        text="Export",
        icon=ft.Icons.SAVE,
        on_click=on_export_click,
        disabled=True
    )

    # デバウンス付きのプレビュー更新処理
    def update_image_preview():
        nonlocal current_image
        print(f"[DEBUG] update_image_preview called, original_image={original_image}")
        if original_image is None:
            print(f"[DEBUG] original_image is None, returning")
            return

        # ローディング表示
        loading_indicator.visible = True
        page.update()

        # スライダーの値を取得
        sat_val = slider_satur.value
        lev_val = int(slider_level.value)
        smt_val = slider_smooth.value
        edg_val = slider_edge.value

        print(f"[DEBUG] Parameters: sat={sat_val}, lev={lev_val}, smt={smt_val}, edg={edg_val}")

        # スライダーの値をテキストに反映
        satur_value_text.value = f"{sat_val:.2f}"
        level_value_text.value = f"{lev_val}"
        smooth_value_text.value = f"{smt_val}"
        edge_value_text.value = f"{edg_val:.2f}"
        satur_value_text.update()
        level_value_text.update()
        smooth_value_text.update()
        edge_value_text.update()

        # 画像処理
        print(f"[DEBUG] Starting postarization...")
        current_image = postarization(
            original_image,
            saturation=sat_val,
            level=lev_val,
            smooth_strength=smt_val,
            edge_strength=edg_val
        )
        print(f"[DEBUG] Postarization complete, image size: {current_image.size}")
        
        # メモリ解放
        gc.collect()
        
        base64_str = pil_to_base64(current_image, "JPEG")
        print(f"[DEBUG] Base64 encoded, length: {len(base64_str)}")
        image_control.src_base64 = base64_str
        image_control.update()
        print(f"[DEBUG] Image control updated")

        # ローディング非表示
        loading_indicator.visible = False
        page.update()

    def on_slider_change(e):
        nonlocal update_timer
        if update_timer:
            update_timer.cancel()
        update_timer = threading.Timer(0.3, update_image_preview)
        update_timer.start()

    # 画像インポート用ファイルピッカー
    upload_folder = "storage/temp"
    os.makedirs(upload_folder, exist_ok=True)
    
    def on_file_pick_result(e: ft.FilePickerResultEvent):
        nonlocal original_image, current_image
        print(f"[DEBUG] on_file_pick_result called: e.files={e.files}")
        if e.files and len(e.files) > 0:
            file_info = e.files[0]
            
            # デスクトップ版: pathが存在する場合は直接読み込み
            if file_info.path:
                print(f"[DEBUG] Desktop mode: path={file_info.path}")
                try:
                    img = Image.open(file_info.path)
                    print(f"[DEBUG] Image opened: size={img.size}, mode={img.mode}")
                    
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                        print(f"[DEBUG] Converted to RGB")
                    original_image = img
                    print(f"[DEBUG] original_image set successfully")
                    
                    # スライダー & Export ボタンを有効化
                    slider_satur.disabled = False
                    slider_level.disabled = False
                    slider_smooth.disabled = False
                    slider_edge.disabled = False
                    export_button.disabled = False

                    # スライダー変更時はデバウンス適用
                    slider_satur.on_change = on_slider_change
                    slider_level.on_change = on_slider_change
                    slider_smooth.on_change = on_slider_change
                    slider_edge.on_change = on_slider_change

                    print(f"[DEBUG] Calling update_image_preview()")
                    update_image_preview()
                    page.update()
                except Exception as ex:
                    print(f"[ERROR] 画像の読み込みに失敗しました: {ex}")
                    traceback.print_exc()
            else:
                # Web版: アップロードを開始
                print(f"[DEBUG] Web mode: starting upload for {file_info.name}")
                upload_list = []
                for f in e.files:
                    upload_list.append(
                        ft.FilePickerUploadFile(
                            f.name,
                            upload_url=page.get_upload_url(f.name, 600),
                        )
                    )
                file_picker_open.upload(upload_list)

    def on_upload_complete(e: ft.FilePickerResultEvent):
        nonlocal original_image, current_image
        print(f"[DEBUG] on_upload_complete called, e={e}")
        
        # アップロード完了後、ファイルが保存されるまで少し待つ
        time.sleep(0.5)
        
        # アップロードされたファイルを読み込む
        upload_list = file_picker_open.result.files if file_picker_open.result else None
        if not upload_list or len(upload_list) == 0:
            print(f"[ERROR] No files uploaded")
            return
            
        file_name = upload_list[0].name
        file_path = os.path.join(upload_folder, file_name)
        print(f"[DEBUG] Looking for uploaded file at: {file_path}")
        
        # ファイルが完全にアップロードされるまで待つ
        max_wait = 10
        waited = 0
        while not os.path.exists(file_path) and waited < max_wait:
            time.sleep(0.1)
            waited += 0.1
        
        if not os.path.exists(file_path):
            print(f"[ERROR] Upload timeout - file not found: {file_path}")
            return
        
        # ファイルが完全に書き込まれるまで追加で待つ
        time.sleep(0.5)
        
        # ファイルタイプの検証
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
        file_ext = os.path.splitext(file_name)[1].lower()
        if file_ext not in allowed_extensions:
            print(f"[ERROR] Invalid file type: {file_ext}")
            return
        
        try:
            print(f"[DEBUG] File found, opening: {file_path}")
            img = Image.open(file_path)
            # 画像を完全に読み込む
            img.load()
            print(f"[DEBUG] Image loaded completely: size={img.size}, mode={img.mode}")
            
            # メモリ節約のためにリサイズ
            img = resize_image_if_needed(img)
                
            if img.mode != "RGB":
                img = img.convert("RGB")
                print(f"[DEBUG] Converted to RGB")
            original_image = img
            print(f"[DEBUG] original_image set successfully")
            
            # スライダー & Export ボタンを有効化
            slider_satur.disabled = False
            slider_level.disabled = False
            slider_smooth.disabled = False
            slider_edge.disabled = False
            export_button.disabled = False

            # スライダー変更時はデバウンス適用
            slider_satur.on_change = on_slider_change
            slider_level.on_change = on_slider_change
            slider_smooth.on_change = on_slider_change
            slider_edge.on_change = on_slider_change

            print(f"[DEBUG] Calling update_image_preview()")
            # 初回表示
            update_image_preview()
            page.update()
        except Exception as ex:
            print(f"[ERROR] 画像の読み込みに失敗しました: {ex}")
            traceback.print_exc()

    file_picker_open = ft.FilePicker(
        on_result=on_file_pick_result,
        on_upload=on_upload_complete
    )
    file_picker_save = ft.FilePicker(
        on_result=on_save_dialog_result
    )
    import_button = ft.ElevatedButton(
        text="Import",
        icon=ft.Icons.UPLOAD_FILE,
        on_click=lambda _: file_picker_open.pick_files(
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["jpg", "jpeg", "png", "bmp", "webp"],
            allow_multiple=False
        )
    )

    # ---- テンプレートボタンの実装 ----
    def apply_template(preset_name: str):
        """
        指定したテンプレート名に対応するパラメータをスライダーに適用し、即時更新。
        """
        if preset_name not in PARAMETER_SETS:
            return
        params = PARAMETER_SETS[preset_name]
        slider_satur.value = params["saturation"]
        slider_level.value = params["level"]
        slider_smooth.value = params["smooth_strength"]
        slider_edge.value = params["edge_strength"]

        # スライダー値を変更したので、すぐに更新処理を走らせる
        update_image_preview()

    # テンプレートボタンのレイアウト
    template_buttons = ft.Row(
        controls=[
            ft.ElevatedButton("default",   on_click=lambda e: apply_template("default")),
            ft.ElevatedButton("realistic", on_click=lambda e: apply_template("realistic")),
            ft.ElevatedButton("anime",     on_click=lambda e: apply_template("anime_style")),
            ft.ElevatedButton("monochro",  on_click=lambda e: apply_template("monochrome")),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
    )

    # ---- レイアウト構築 ----
    # 右側のパラメータパネル
    param_panel = ft.Column(
        controls=[
            ft.Text("saturation: 彩度の倍率"),
            ft.Row([slider_satur, satur_value_text]),
            ft.Text("level: ポスタリゼーションの色レベル"),
            ft.Row([slider_level, level_value_text]),
            ft.Text("smooth_strength: 平滑化の強さ (0-200)"),
            ft.Row([slider_smooth, smooth_value_text]),
            ft.Text("edge_strength: エッジ保持の強さ (0.0-2.0)"),
            ft.Row([slider_edge, edge_value_text]),
        ],
        spacing=10,
    )

    # 全体レイアウト（左:プレビュー, 右:スライダー）
    top_area = ft.Row(
        controls=[
            image_stack,
            param_panel,
        ],
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.START
    )

    # 下部のテンプレートボタン + Import ボタン
    bottom_area = ft.Row(
        controls=[
            template_buttons,
            import_button,
            export_button,
        ],
        spacing=30,
        alignment=ft.MainAxisAlignment.CENTER
    )

    page.overlay.append(file_picker_open)
    page.overlay.append(file_picker_save)

    # ページに追加
    page.add(
        ft.Column(
            controls=[
                top_area,
                # ft.Text("パラメータ テンプレート"),
                bottom_area,
            ],
            spacing=20
        )
    )


ft.app(target=main)
