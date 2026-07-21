#!/bin/bash
# ====================================================================
# build.sh - Wiki (Astro) ローカルビルドスクリプト
# ====================================================================
# 用途: 開発者がローカル環境でWikiのMarkdownを編集した後、
#       Astroの静的ビルドを実行し、生成物(wiki/dist)をGitにコミットする。
#
# !! 注意 !!
# このスクリプトは本番デプロイ時に自動実行されることを前提としていません。
# 本番サーバーにはNode.js/npmは不要です。
# wiki/dist はビルド済みの状態でGitリポジトリにコミットされており、
# 本番サーバーはFlask(Python)のみでWikiの静的ファイルを配信します。
# ====================================================================

set -e

echo "=== Building pawapuro-wiki (Astro) ==="
cd wiki
npm install
npm run build
cd ..

echo ""
echo "=== Wiki build complete! ==="
echo ""
echo "次の手順でビルド結果をコミットしてください:"
echo "  git add wiki/dist"
echo "  git commit -m 'build: update wiki static files'"
echo ""
