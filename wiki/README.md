# パワプロ2026-2027 栄冠ナイン(3年縛り)攻略Wiki

`quiz-app` リポジトリ内に同居する Astro ベースの静的サイト生成 (SSG) プロジェクトです。
Flask アプリ（`app.py`）が `/wiki/` パスでこの `dist/` フォルダ内の HTML を配信します。

## アーキテクチャ

```
quiz-app/             ← Flask アプリ本体
├── app.py            ← /wiki/* を wiki/dist から配信
├── wiki/             ← 本ディレクトリ (Astro プロジェクト)
│   ├── src/pages/wiki/  ← Markdown コンテンツ
│   ├── dist/            ← ビルド済み HTML/CSS/JS (Git にコミット済み)
│   └── ...
```

## ⚠️ デプロイ方式について

**本番サーバーに Node.js / npm は不要です。**

`wiki/dist/` はビルド済みの静的ファイルとして Git リポジトリにコミットされています。
Flask (`app.py`) が `send_from_directory` を使ってこのフォルダの中身をそのまま配信するため、
本番環境に必要なのは Python / Flask のみです。

## 📝 コンテンツ更新時の手順

Wiki のコンテンツ（`src/pages/wiki/*.md`）を追加・編集した場合は、
**ローカル環境で以下のコマンドを実行して `dist/` を再ビルドし、コミットしてください。**

```bash
# 1. Astro をビルド
cd wiki
npm install
npm run build

# 2. ビルド結果を Git にコミット
cd ..
git add wiki/dist
git commit -m "build: update wiki static files"
git push
```

または、リポジトリルートに用意してある `build.sh` を使えます:

```bash
bash build.sh
# その後 git add / commit / push
```

## 🧞 開発用コマンド

すべてのコマンドは `wiki/` ディレクトリ内で実行してください:

| コマンド | 説明 |
| :--- | :--- |
| `npm install` | 依存パッケージのインストール |
| `npm run dev` | ローカル開発サーバーを起動 (`localhost:4321`) |
| `npm run build` | 本番用の静的ファイルを `./dist/` に出力 |
| `npm run preview` | ビルド結果をローカルでプレビュー |
