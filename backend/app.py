from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import sys

# パスを追加してollama_clientをインポート可能にする
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ollama_client import OllamaClient
from document_search import DocumentSearch

# テンプレートと静的ファイルのパスを設定
template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'template')
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
CORS(app)

# 環境判定
IS_VERCEL = os.getenv('VERCEL') == '1'

# Ollamaクライアントの初期化
if IS_VERCEL:
    # Vercel環境: 外部Ollamaサーバーを使用
    ollama_api_url = os.getenv('OLLAMA_API_URL', 'http://localhost:11434')
    ollama_client = OllamaClient(None, api_url=ollama_api_url)
    print(f"Vercel環境: Ollama API URL = {ollama_api_url}")
else:
    # ローカル環境
    ollama_path = r"C:\Users\e9uch\AppData\Local\Programs\Ollama\ollama.exe"
    ollama_client = OllamaClient(ollama_path)
    print("ローカル環境: ローカルのOllamaを使用")

# ドキュメント検索の初期化
docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs')
document_search = DocumentSearch(docs_dir)

# 起動時にモデルを確認・ダウンロード（ローカル環境のみ）
if not IS_VERCEL:
    print("Ollamaモデルを確認しています...")
    print("※ モデルは一度ダウンロードされれば、次回以降は自動的に使用されます。")
    print("※ すべての処理はローカルで完結し、データは外部に送信されません。\n")
    try:
        ollama_client.ensure_model()
    except Exception as e:
        print(f"モデルの確認中にエラーが発生しました: {e}")
        print("アプリケーションは続行しますが、モデルが利用できない可能性があります。")
else:
    print("Vercel環境: 外部Ollamaサーバーを使用します")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """チャットボットAPI"""
    data = request.json
    message = data.get('message', '')
    function_type = data.get('function_type', 'chatbot')
    
    try:
        # ドキュメント検索（チャットボット機能の場合）
        sources = []
        if function_type == 'chatbot':
            # 質問に関連するドキュメントを検索
            search_results = document_search.search(message, max_results=3)
            sources = []
            for result in search_results:
                # ファイル全体が返された場合はそのまま、部分の場合は要約
                content = result['content']
                if len(content) > 500:
                    # 長い場合は最初の部分と最後の部分を表示
                    sources.append({
                        'title': result['title'],
                        'content': content[:400] + '\n\n... (中略) ...\n\n' + content[-200:],
                        'line': result.get('line', 0),
                        'full_content': content  # 完全な内容も保持
                    })
                else:
                    sources.append({
                        'title': result['title'],
                        'content': content,
                        'line': result.get('line', 0)
                    })
            
            # 検索結果をコンテキストに含めて質問を拡張
            if sources:
                context = "以下のドキュメントの内容を参照してください:\n\n"
                for i, source in enumerate(sources, 1):
                    context += f"【{source['title']}】\n{source['content']}\n\n"
                enhanced_message = f"{context}質問: {message}\n\n上記のドキュメントの内容に基づいて、質問に日本語で回答してください。ドキュメントに記載されていない内容については推測せず、「ドキュメントに記載がありません」と答えてください。"
            else:
                enhanced_message = message
        else:
            enhanced_message = message
        
        # 機能タイプに応じて処理を分岐
        if function_type == 'chatbot':
            response = ollama_client.chat(enhanced_message if sources else message)
        elif function_type == 'daily_report':
            response = ollama_client.generate_daily_report(message)
        elif function_type == 'anomaly_detection':
            response = ollama_client.detect_anomaly(message)
        elif function_type == 'production_plan':
            response = ollama_client.generate_production_plan(message)
        else:
            response = ollama_client.chat(message)
        
        return jsonify({
            'success': True,
            'response': response,
            'sources': sources
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/documents', methods=['GET'])
def get_documents():
    """利用可能なドキュメント一覧を取得"""
    docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs')
    documents = []
    
    if os.path.exists(docs_dir):
        for filename in os.listdir(docs_dir):
            if filename.endswith(('.txt', '.md', '.pdf')):
                documents.append({
                    'name': filename,
                    'path': f'docs/{filename}'
                })
    
    return jsonify({'documents': documents})

@app.route('/api/documents/reload', methods=['POST'])
def reload_documents():
    """ドキュメントを再読み込み"""
    try:
        document_search.reload()
        return jsonify({'success': True, 'message': 'ドキュメントを再読み込みしました'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/documents/<filename>', methods=['GET'])
def get_document(filename):
    """ドキュメントの内容を取得"""
    import urllib.parse
    
    # セキュリティ: パストラバーサル攻撃を防ぐ
    filename = os.path.basename(filename)
    current_docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs')
    filepath = os.path.join(current_docs_dir, filename)
    
    # 親ディレクトリへの移動を防ぐ
    if not os.path.abspath(filepath).startswith(os.path.abspath(current_docs_dir)):
        return jsonify({'error': 'Invalid file path'}), 400
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    if not filename.endswith(('.txt', '.md')):
        return jsonify({'error': 'Unsupported file type'}), 400
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            'success': True,
            'filename': filename,
            'content': content
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

