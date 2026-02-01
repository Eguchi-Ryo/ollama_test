# Vercelデプロイメント手順

## 前提条件

1. **Ollamaサーバーの準備**
   - Vercelのサーバーレス環境ではOllamaを直接実行できません
   - 別のサーバー（Railway、Render、自社サーバーなど）でOllamaを起動する必要があります

## デプロイ手順

### 1. Ollamaサーバーのセットアップ

#### オプションA: RailwayでOllamaをホスト
```bash
# RailwayにOllamaコンテナをデプロイ
# docker-compose.ymlを作成してデプロイ
```

#### オプションB: RenderでOllamaをホスト
```bash
# RenderでWebサービスとしてOllamaを起動
```

#### オプションC: 自社サーバー
```bash
# 社内サーバーにOllamaをインストール
# ファイアウォールでアクセス制限
```

### 2. Vercel環境変数の設定

Vercelのダッシュボードで以下を設定：

```
OLLAMA_API_URL=https://your-ollama-server.com
VERCEL=1
```

### 3. ドキュメントの配置

- `docs`フォルダをGitリポジトリにコミットしてください
- VercelはGitリポジトリからデプロイするため、`docs`フォルダが含まれている必要があります

### 4. デプロイ

```bash
# Vercel CLIを使用
vercel

# またはGitHubと連携して自動デプロイ
# GitHubリポジトリをVercelに接続
```

## トラブルシューティング

### ビルドエラーが発生する場合

1. **Pythonバージョンの確認**
   - `vercel.json`で`PYTHON_VERSION`を確認
   - Python 3.11を推奨

2. **依存関係の確認**
   - `requirements.txt`が正しく配置されているか確認

3. **パスの確認**
   - `backend/app.py`が正しいパスにあるか確認
   - `vercel.json`の`src`パスを確認

### Ollamaに接続できない場合

1. **環境変数の確認**
   - `OLLAMA_API_URL`が正しく設定されているか確認
   - Ollamaサーバーが起動しているか確認

2. **ネットワークの確認**
   - Ollamaサーバーがインターネットからアクセス可能か確認
   - ファイアウォール設定を確認

### ドキュメントが読み込めない場合

1. **Gitリポジトリの確認**
   - `docs`フォルダがGitにコミットされているか確認
   - `.gitignore`で除外されていないか確認

## 注意事項

- Vercelのサーバーレス環境では、起動時にOllamaモデルのダウンロードは行いません
- 外部Ollamaサーバーが利用可能である必要があります
- ドキュメントはGitリポジトリに含める必要があります

