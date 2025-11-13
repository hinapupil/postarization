import flet as ft
from postarization import postarization
from PIL import Image
import base64
from io import BytesIO
import threading

# 例として同ファイル内に定義しておきます
PARAMETER_SETS = {
    "default":    {"saturation": 2,   "level": 8,  "smooth_strength": 50, "edge_strength": 0.4},
    "realistic":  {"saturation": 1.5, "level": 12, "smooth_strength": 70, "edge_strength": 0.3},
    "anime_style":{"saturation": 2.5, "level": 6,  "smooth_strength": 40, "edge_strength": 0.5},
    "monochrome": {"saturation": 0, "level": 4,  "smooth_strength": 80, "edge_strength": 0.2},
    "novel_game": {"saturation": 1.6, "level": 8, "smooth_strength": 68, "edge_strength": 0.8},
}

def main(page: ft.Page):
    # page.window_maximized = True
    # page.window_full_screen = True
    page.title = "Postarization Filter"
    page.scroll = "auto"

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

    # エクスポート用ファイルピッカー
    def on_save_dialog_result(e: ft.FilePickerResultEvent):
        if e.path:
            save_path = e.path
            if not (save_path.lower().endswith(".jpg") or save_path.lower().endswith(".jpeg") or save_path.lower().endswith(".png")):
                save_path += ".png"
            try:
                if original_image:
                    # テンプレートパラメータを適用した最終画像を保存
                    processed_full = postarization(
                        original_image,
                        saturation=slider_satur.value,
                        level=int(slider_level.value),
                        smooth_strength=slider_smooth.value,
                        edge_strength=slider_edge.value
                    )
                    processed_full.save(save_path, format="PNG")
                    print(f"画像を保存しました: {save_path}")
            except Exception as ex:
                print(f"画像の保存に失敗しました: {ex}")

    file_picker_save = ft.FilePicker(on_result=on_save_dialog_result)
    export_button = ft.ElevatedButton(
        text="Export",
        icon=ft.Icons.SAVE,
        on_click=lambda _: file_picker_save.save_file(
            file_name="output.png",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["png"]
        ),
        disabled=True
    )

    # デバウンス付きのプレビュー更新処理
    def update_image_preview():
        nonlocal current_image
        if original_image is None:
            return

        # ローディング表示
        loading_indicator.visible = True
        page.update()

        # スライダーの値を取得
        sat_val = slider_satur.value
        lev_val = int(slider_level.value)
        smt_val = slider_smooth.value
        edg_val = slider_edge.value

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
        current_image = postarization(
            original_image,
            saturation=sat_val,
            level=lev_val,
            smooth_strength=smt_val,
            edge_strength=edg_val
        )
        image_control.src_base64 = pil_to_base64(current_image, "JPEG")
        image_control.update()

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
    def on_file_pick_result(e: ft.FilePickerResultEvent):
        nonlocal original_image, current_image
        if e.files and len(e.files) > 0:
            file_path = e.files[0].path
            try:
                img = Image.open(file_path)
                if img.mode != "RGB":
                    img = img.convert("RGB")
                original_image = img
            except Exception as ex:
                print(f"画像の読み込みに失敗しました: {ex}")
                return
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

            # 初回表示
            update_image_preview()
            page.update()

    file_picker_open = ft.FilePicker(on_result=on_file_pick_result)
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
