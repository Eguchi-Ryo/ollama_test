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

# Ollamaクライアントの初期化
ollama_path = r"C:\Users\e9uch\AppData\Local\Programs\Ollama\ollama.exe"
ollama_client = OllamaClient(ollama_path)

# ドキュメント検索の初期化
docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs')
document_search = DocumentSearch(docs_dir)

# 起動時にモデルを確認・ダウンロード
print("Ollamaモデルを確認しています...")
print("※ モデルは一度ダウンロードされれば、次回以降は自動的に使用されます。")
print("※ すべての処理はローカルで完結し、データは外部に送信されません。\n")
try:
    ollama_client.ensure_model()
except Exception as e:
    print(f"モデルの確認中にエラーが発生しました: {e}")
    print("アプリケーションは続行しますが、モデルが利用できない可能性があります。")

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
            sources = [
                {
                    'title': result['title'],
                    'content': result['content'][:300] + '...' if len(result['content']) > 300 else result['content'],
                    'line': result.get('line', 0)
                }
                for result in search_results
            ]
            
            # 検索結果をコンテキストに含めて質問を拡張
            if sources:
                context = "\n\n参照ドキュメント:\n"
                for i, source in enumerate(sources, 1):
                    context += f"{i}. {source['title']}:\n{source['content']}\n\n"
                enhanced_message = f"{context}\n質問: {message}\n\n上記のドキュメントを参照しながら回答してください。"
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)

