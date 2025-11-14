#!/bin/bash

# iOS Build Script for Postarization App
# このスクリプトは iOS アプリのビルドを簡単にするためのヘルパースクリプトです

set -e  # エラーが発生したら即座に終了

# 色付き出力用の定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Postarization iOS Build Script ===${NC}"

# macOS チェック
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}Error: iOS builds can only be created on macOS.${NC}"
    exit 1
fi

# Flet がインストールされているかチェック
if ! command -v flet &> /dev/null; then
    echo -e "${RED}Error: 'flet' command not found. Please install Flet first.${NC}"
    echo "Install with: pip install flet"
    exit 1
fi

# ビルドタイプの選択
echo ""
echo "Select build type:"
echo "1) Development (debugging) - for testing on your device"
echo "2) Ad Hoc (release-testing) - for distribution to specific devices"
echo "3) App Store Connect (app-store-connect) - for App Store submission"
echo ""
read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        EXPORT_METHOD="debugging"
        PROFILE_NAME="Postarization Development"
        CERT_TYPE="Apple Development"
        NEEDS_TEAM_ID=false
        echo -e "${GREEN}Building for development...${NC}"
        ;;
    2)
        EXPORT_METHOD="release-testing"
        PROFILE_NAME="Postarization AdHoc"
        CERT_TYPE="Apple Distribution"
        NEEDS_TEAM_ID=true
        echo -e "${GREEN}Building for Ad Hoc distribution...${NC}"
        ;;
    3)
        EXPORT_METHOD="app-store-connect"
        PROFILE_NAME="Postarization AppStore"
        CERT_TYPE="Apple Distribution"
        NEEDS_TEAM_ID=true
        echo -e "${GREEN}Building for App Store Connect...${NC}"
        ;;
    *)
        echo -e "${RED}Invalid choice. Exiting.${NC}"
        exit 1
        ;;
esac

# Team ID が必要な場合は入力を求める
TEAM_ID_ARG=""
if [ "$NEEDS_TEAM_ID" = true ]; then
    echo ""
    read -p "Enter your Apple Developer Team ID (10 characters): " TEAM_ID
    if [ -z "$TEAM_ID" ]; then
        echo -e "${RED}Error: Team ID is required for this build type.${NC}"
        exit 1
    fi
    TEAM_ID_ARG="--ios-team-id $TEAM_ID"
fi

# Provisioning Profile 名の確認
echo ""
read -p "Enter Provisioning Profile name (default: $PROFILE_NAME): " CUSTOM_PROFILE
if [ ! -z "$CUSTOM_PROFILE" ]; then
    PROFILE_NAME="$CUSTOM_PROFILE"
fi

# ビルド実行
echo ""
echo -e "${YELLOW}Building iOS app with the following settings:${NC}"
echo "  Export Method: $EXPORT_METHOD"
echo "  Provisioning Profile: $PROFILE_NAME"
echo "  Signing Certificate: $CERT_TYPE"
if [ "$NEEDS_TEAM_ID" = true ]; then
    echo "  Team ID: $TEAM_ID"
fi
echo ""

read -p "Proceed with build? (y/n): " confirm
if [[ $confirm != [yY] ]]; then
    echo "Build cancelled."
    exit 0
fi

echo -e "${GREEN}Starting build...${NC}"

# ビルドコマンドの実行
flet build ipa \
    --ios-export-method "$EXPORT_METHOD" \
    --ios-provisioning-profile "$PROFILE_NAME" \
    --ios-signing-certificate "$CERT_TYPE" \
    $TEAM_ID_ARG

# ビルド成功
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Build completed successfully!${NC}"
    echo ""
    echo "The .ipa file should be located in:"
    echo "  build/ios/ipa/"
    echo ""
    
    if [ "$EXPORT_METHOD" == "debugging" ]; then
        echo -e "${YELLOW}Next steps:${NC}"
        echo "1. Connect your iOS device to your Mac"
        echo "2. Open Apple Configurator"
        echo "3. Drag and drop the .ipa file onto your device"
        echo "4. Trust the developer profile on your device"
    elif [ "$EXPORT_METHOD" == "app-store-connect" ]; then
        echo -e "${YELLOW}Next steps:${NC}"
        echo "1. Open Transporter app"
        echo "2. Sign in with your Apple Developer account"
        echo "3. Drag and drop the .ipa file to upload"
        echo "4. Verify and deliver to App Store Connect"
    fi
else
    echo ""
    echo -e "${RED}✗ Build failed. Please check the error messages above.${NC}"
    exit 1
fi
