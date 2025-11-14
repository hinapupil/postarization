# Postarization Filter

画像をアニメ風に変換するGUIアプリケーションです。インタラクティブにパラメータを調整しながらリアルタイムでプレビューできます。

## 機能

- 画像のインポート（ローカルファイル選択）
  - 対応形式: JPEG, PNG, WebP
- リアルタイムプレビュー
- 5種類のパラメータテンプレート（default, realistic, anime_style, monochrome, novel_game）
- 4つの調整可能なパラメータ:
  - 彩度 (Saturation)
  - 色レベル (Level)
  - 平滑化の強さ (Smooth Strength)
  - エッジ強度 (Edge Strength)
- PNG形式でのエクスポート

## 必要な環境

- Python 3.9以上
- 依存ライブラリ: Flet, Pillow, OpenCV

**注意:** WebP形式の画像を使用する場合、Pillowがlibwebpサポート付きでインストールされている必要があります。通常、pipでインストールされるPillowには含まれていますが、環境によってはlibwebpが不足している場合があります。

## 開発環境でのアプリ実行

### デスクトップアプリとして実行

```bash
flet run --module-name src/main.py
```

### Web版として実行

```bash
flet run --web --module-name src/main.py
```

## リリースビルド

### Windows向け実行可能ファイルのビルド

```bash
flet build windows --module-name src/main.py
```

ビルド完了後、`build/windows`ディレクトリに実行可能ファイルが生成されます。

### その他のプラットフォーム

```bash
# macOS
flet build macos --module-name src/main.py

# Linux
flet build linux --module-name src/main.py

# Webアプリ
flet build web --module-name src/main.py
```

詳細は[Fletビルドガイド](https://flet.dev/docs/publish/)を参照してください。

### iOS

```
flet build ipa -v
```

For more details on building and signing `.ipa`, refer to the [iOS Packaging Guide](https://flet.dev/docs/publish/ios/).

### macOS

```
flet build macos -v
```

For more details on building macOS package, refer to the [macOS Packaging Guide](https://flet.dev/docs/publish/macos/).

### Linux

```
flet build linux -v
```

For more details on building Linux package, refer to the [Linux Packaging Guide](https://flet.dev/docs/publish/linux/).

### Windows

```
flet build windows -v
```

For more details on building Windows package, refer to the [Windows Packaging Guide](https://flet.dev/docs/publish/windows/).