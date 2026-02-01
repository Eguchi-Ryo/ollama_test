"""
製造現場AIアシスタント 起動スクリプト
"""
import os
import sys

# backendディレクトリをパスに追加
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

# Flaskアプリをインポート（この時点でモデル確認が実行される）
from app import app

if __name__ == '__main__':
    print("=" * 50)
    print("製造現場AIアシスタントを起動しています...")
    print("=" * 50)
    print("ブラウザで http://localhost:5000 にアクセスしてください")
    print("=" * 50)
    app.run(debug=True, port=5000, host='127.0.0.1')

