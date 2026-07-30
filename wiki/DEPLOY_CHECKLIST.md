# デプロイ後 手動確認チェックリスト

## デプロイ手順（2026-07 確立）
1. 変更はすべてWindows（C:\Users\miyamoto\quiz-app）で行う。Piでは編集しない
2. `.\deploy-wiki.ps1` を実行（ビルド→commit→push）
3. Piのsystemdタイマー wiki-deploy.timer が3分以内に自動pull
4. **wiki配下の変更のみ自動反映。app.py 等のPythonコードを変更した場合は
   `sudo systemctl restart flask-app.service` を手動実行すること**
5. 確認は必ずシークレットウィンドウで行う（ブラウザキャッシュ対策）

本番環境（Raspberry Pi / VPS）へデプロイした後に、以下の項目を上から順に確認してください。

## 1. Wikiトップページの表示

- [ ] `https://das-mymt.com/wiki/` にアクセスし、Wikiのトップページが正しく表示されること
- [ ] 全10カテゴリへのリンクがトップページ上に表示されていること

## 2. 既存クイズ機能の動作確認

- [ ] `https://das-mymt.com/` にアクセスし、ログイン画面が正しく表示される
- [ ] Googleログインフローが正常に完了する（ログインボタン → Google認証 → リダイレクト → ダッシュボード表示）
- [ ] CSVアップロード機能が動作する（テスト用CSVを使用）
- [ ] クイズ実施画面が表示され、問題・解答が正しく出力される
- [ ] PDF生成機能が動作する（ダウンロードが開始される）
- [ ] ログアウトが正常に機能する

## 3. 全10カテゴリページの個別確認

各URLにアクセスし、ページが正しく表示されること（タイトル・本文・表・画像が読み込まれること）を確認してください。

- [ ] [1. モード基本仕様と設定](https://das-mymt.com/wiki/basic-rules)
- [ ] [2. 年間スケジュール](https://das-mymt.com/wiki/schedule)
- [ ] [3. 都道府県リスト・転生OB](https://das-mymt.com/wiki/prefectures)
- [ ] [4. すごろく(マス)と進行アイコン・器材](https://das-mymt.com/wiki/board-squares)
- [ ] [5. 性格と固有戦術 / 伝令](https://das-mymt.com/wiki/personalities)
- [ ] [6. 育成方針](https://das-mymt.com/wiki/training-policy)
- [ ] [7. カード効果・特殊能力](https://das-mymt.com/wiki/card-effects)
- [ ] [8. 試合の立ち回り](https://das-mymt.com/wiki/match-strategy)
- [ ] [9. 周辺システム](https://das-mymt.com/wiki/other-systems)
- [ ] [10. 大会・甲子園](https://das-mymt.com/wiki/tournaments)

## 4. 画像の表示確認

- [ ] 各カテゴリページに挿入されている画像がすべてローカルから正しく表示されること
- [ ] ブラウザのDevToolsのNetworkタブで、画像リクエストが外部サイト(Game8等)に飛んでいないこと
- [ ] 画像の読み込みに404エラーがないこと（DevToolsのConsoleタブで確認）

## 5. レスポンシブ対応

- [ ] PCブラウザ（横幅1280px以上）で表示崩れがないこと
- [ ] タブレット幅（768px〜1024px）で表示崩れがないこと
- [ ] モバイル幅（375px〜414px）で以下が正しく表示されること：
  - [ ] ヘッダーのナビゲーション
  - [ ] テーブル（横スクロールまたは折り返し）
  - [ ] `<details>` タグの展開・折りたたみ

## 6. 内部リンクの確認

- [ ] 各カテゴリページからトップページ（`/wiki/`）に戻れること
- [ ] カテゴリ間の内部リンク（例: `card-effects` 内の `personalities` へのリンク等）が機能すること
- [ ] ページ内アンカーリンクが正しく動作すること

## 7. パフォーマンス・セキュリティ

- [ ] 各ページの初回読み込みが5秒以内に完了すること
- [ ] ブラウザのDevToolsで混在コンテンツ（Mixed Content）警告が出ていないこと
- [ ] `https://das-mymt.com/wiki/` に直接アクセスしてもログインを要求されないこと（非ログインで閲覧可能）

## 問題が見つかった場合の対応

1. **Wikiが404になる場合**: `wiki/dist/` ディレクトリがサーバー上に正しくデプロイされているか確認。`gunicorn` の再起動が必要な場合あり。
2. **画像が表示されない場合**: `wiki/dist/images/` ディレクトリとその中身がサーバー上に存在するか確認。
3. **既存クイズ機能が壊れた場合**: `git diff main -- app.py` で差分を確認し、Wikiルート以外の変更がないか検証。最悪の場合は `git revert` でロールバック。
