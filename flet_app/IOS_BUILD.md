# iOS アプリとしてビルド・公開する手順

このドキュメントでは、Flet アプリを iOS アプリとして公開するための手順を説明します。

## 前提条件

### 必須環境
- macOS（iOS ビルドは macOS でのみ可能）
- Xcode 15 以降
- CocoaPods 1.16 以降
- Apple Developer Program のアカウント

### Rosetta 2（Apple Silicon Mac の場合）
```bash
sudo softwareupdate --install-rosetta --agree-to-license
```

### CocoaPods のインストール
```bash
sudo gem install cocoapods
```

## Apple Developer での準備

### 1. App ID の作成
1. [Apple Developer Portal](https://developer.apple.com/account/resources/identifiers/list) にアクセス
2. 「+」ボタンをクリック
3. 「App IDs」を選択して続行
4. Description: `Postarization Filter`
5. Bundle ID: `com.kemuri.postarization`（明示的 Bundle ID を選択）
6. 必要なサービスを選択（Push Notifications など）
7. 続行してレジスター

### 2. 署名証明書の作成

#### CSR（証明書署名要求）の生成
1. Keychain Access を開く（Command + Space で検索）
2. メニューから `Keychain Access` → `Certificate Assistant` → `Request a Certificate From a Certificate Authority...`
3. 入力:
   - User Email Address: あなたの Apple Developer メールアドレス
   - Common Name: `Postarization Distribution`
   - CA Email Address: 空白のまま
   - Request is for: `Saved to disk` を選択
4. 続行して `.certSigningRequest` ファイルを保存

#### Apple Developer Portal で証明書を作成
1. [Certificates Page](https://developer.apple.com/account/resources/certificates/list) にアクセス
2. 「+」ボタンをクリック
3. 証明書タイプを選択:
   - **開発用**: `Apple Development`
   - **配布用**: `Apple Distribution`
4. 作成した CSR ファイルをアップロード
5. 証明書をダウンロード（`.cer` ファイル）
6. ダウンロードしたファイルをダブルクリックして Keychain Access にインストール

### 3. Provisioning Profile の作成

#### 開発用 Profile（デバイスでのテスト用）
1. [Provisioning Profiles](https://developer.apple.com/account/resources/profiles/list) にアクセス
2. 「+」ボタンをクリック
3. `iOS App Development` を選択
4. App ID: `com.kemuri.postarization` を選択
5. 開発証明書を選択
6. テストするデバイスを選択
7. Profile Name: `Postarization Development`
8. ダウンロードして次のコマンドでインストール:

```bash
# Profile UUID を取得
profile_uuid=$(security cms -D -i ~/Downloads/Postarization_Development.mobileprovision | xmllint --xpath "string(//key[.='UUID']/following-sibling::string[1])" -)
echo $profile_uuid

# Profile をインストール
cp ~/Downloads/Postarization_Development.mobileprovision ~/Library/MobileDevice/Provisioning\ Profiles/${profile_uuid}.mobileprovision
```

#### App Store 用 Profile（ストア配布用）
1. 同様の手順で `App Store` を選択して作成
2. Profile Name: `Postarization AppStore`

## ビルド方法

### 開発用ビルド（デバイステスト用）
```bash
cd flet_app
flet build ipa --ios-export-method debugging --ios-provisioning-profile "Postarization Development"
```

### Ad Hoc ビルド（特定デバイスへの配布用）
```bash
cd flet_app
flet build ipa \
  --ios-export-method release-testing \
  --ios-provisioning-profile "Postarization AdHoc" \
  --ios-signing-certificate "Apple Distribution" \
  --ios-team-id "YOUR_TEAM_ID"
```

### App Store Connect 用ビルド
```bash
cd flet_app
flet build ipa \
  --ios-export-method app-store-connect \
  --ios-provisioning-profile "Postarization AppStore" \
  --ios-signing-certificate "Apple Distribution" \
  --ios-team-id "YOUR_TEAM_ID"
```

**注意**: `YOUR_TEAM_ID` は Apple Developer Portal で確認できる 10 桁の Team ID に置き換えてください。

## デバイスへのインストール（テスト用）

### Apple Configurator を使用
1. [Apple Configurator](https://apps.apple.com/ca/app/apple-configurator/id1037126344?mt=12) を App Store からインストール
2. iOS デバイスを USB ケーブルで Mac に接続
3. Apple Configurator を起動
4. ビルドした `.ipa` ファイルをデバイスにドラッグ＆ドロップ
5. iOS デバイスで: `設定` → `一般` → `VPN とデバイス管理` → Developer Profile を信頼

## App Store Connect へのアップロード

### Transporter を使用
1. [Transporter](https://apps.apple.com/us/app/transporter/id1450874784) を App Store からインストール
2. Transporter を起動して Apple Developer アカウントでサインイン
3. `.ipa` ファイルをドラッグ＆ドロップ
4. 「...」ボタンをクリックして `Verify` を選択
5. 検証成功後、`Deliver` をクリックしてアップロード
6. [App Store Connect](https://appstoreconnect.apple.com/) でビルドを確認

## トラブルシューティング

### ビルドエラー
- Xcode が最新版か確認
- CocoaPods が正しくインストールされているか確認: `pod --version`
- 証明書と Provisioning Profile が正しくインストールされているか確認

### インストールできない
- Provisioning Profile にデバイスの UDID が登録されているか確認
- デバイスで Developer Profile を信頼したか確認

### バイナリパッケージの互換性
このアプリでは以下のバイナリパッケージを使用しています:
- `opencv-python-headless`: iOS 対応ビルドが必要
- `numpy`: iOS 対応版が必要
- `Pillow`: iOS 対応版が必要

もし依存関係のエラーが出る場合は、iOS 対応のホイールが存在するか [Flet Binary Packages](https://flet.dev/docs/reference/binary-packages-android-ios) で確認してください。

## 参考資料
- [Flet iOS 公開ドキュメント](https://flet.dev/docs/publish/ios/)
- [Apple Developer Documentation](https://developer.apple.com/documentation/)
- [App Store Connect](https://appstoreconnect.apple.com/)
