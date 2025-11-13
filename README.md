# SimpleAnimeFilter

画像をアニメ風に変換するPythonアプリケーション集です。
CLIバッチ処理版とGUIインタラクティブ版の2種類を提供しています。

---

## 📁 プロジェクト構成

### 1️⃣ **cli_app** - CLIバッチ処理版
コマンドラインで複数の画像を一括変換します。

**特徴:**
- `input/`フォルダの全画像を一括処理
- 5種類のプリセット（default, realistic, anime_style, monochrome, novel_game）
- 各プリセットごとに`output/`配下に保存

詳細は [cli_app/README.md](cli_app/README.md) を参照してください。

### 2️⃣ **flet_app** - GUIインタラクティブ版
リアルタイムプレビューしながらパラメータを調整できるGUIアプリケーションです。

**特徴:**
- リアルタイムプレビュー
- スライダーで4つのパラメータを調整可能
- 5種類のテンプレートプリセット
- Windows/macOS/Linux向けにビルド可能

詳細は [flet_app/README.md](flet_app/README.md) を参照してください。

---

## 🚀 クイックスタート

### CLI版（バッチ処理）
```bash
cd cli_app
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python main.py
```

### GUI版（インタラクティブ）
```bash
cd flet_app
flet run --module-name src/main.py
```

---

## 📋 必要な環境
- **Python 3.9以上**
- 依存ライブラリ: OpenCV, Pillow, Flet (GUI版のみ)

---

## 📝 ライセンス
このプロジェクトはMITライセンスの下で公開されています。
詳細は [LICENSE](cli_app/LICENSE) を参照してください。

---

## 🎉 コントリビューション
バグ報告や機能提案は [Issues](https://github.com/hinapupil/SimpleAnimeFilter/issues) へお願いします。
プルリクエストも歓迎します！
