"""
ドキュメント検索機能
ローカル完結でドキュメントを検索し、関連する部分を抽出
"""
import os
import re
from typing import List, Dict

class DocumentSearch:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir
        self.documents_cache = {}
        self._load_documents()
    
    def _load_documents(self):
        """ドキュメントを読み込んでキャッシュ"""
        if not os.path.exists(self.docs_dir):
            return
        
        for filename in os.listdir(self.docs_dir):
            if filename.endswith(('.txt', '.md')):
                filepath = os.path.join(self.docs_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        self.documents_cache[filename] = {
                            'name': filename,
                            'content': content,
                            'lines': content.split('\n')
                        }
                except Exception as e:
                    print(f"ドキュメント読み込みエラー ({filename}): {e}")
    
    def search(self, query: str, max_results: int = 3) -> List[Dict]:
        """
        クエリに関連するドキュメントの部分を検索
        
        Args:
            query: 検索クエリ
            max_results: 最大結果数
        
        Returns:
            関連するドキュメントの部分のリスト
        """
        if not query or not self.documents_cache:
            return []
        
        # ファイル名の完全一致をチェック（「○○について教えて」などのパターン）
        query_lower = query.lower()
        for filename, doc_data in self.documents_cache.items():
            filename_lower = filename.lower()
            filename_base = filename_lower.replace('.txt', '').replace('.md', '')
            
            # ファイル名が質問に含まれている場合、そのファイル全体を返す
            if filename_base in query_lower or filename_lower in query_lower:
                return [{
                    'title': doc_data['name'],
                    'content': doc_data['content'],  # ファイル全体
                    'line': 1,
                    'score': 1000  # 最高スコア
                }]
        
        # クエリをキーワードに分割（日本語も含む）
        keywords = []
        # 英数字の単語
        keywords.extend(re.findall(r'\w+', query_lower))
        # 日本語の文字列（2文字以上）
        keywords.extend(re.findall(r'[ぁ-んァ-ヶー一-龠々]+', query))
        
        if not keywords:
            return []
        
        results = []
        
        for filename, doc_data in self.documents_cache.items():
            content = doc_data['content']
            content_lower = content.lower()
            lines = doc_data['lines']
            filename_lower = filename.lower()
            
            # ファイル名も検索対象に含める
            filename_score = 0
            for keyword in keywords:
                if keyword in filename_lower:
                    filename_score += 10  # ファイル名マッチは高スコア
            
            # キーワードの出現回数をカウント
            content_score = sum(content_lower.count(keyword.lower()) for keyword in keywords)
            
            total_score = content_score + filename_score
            
            if total_score > 0:
                # 関連する行を抽出
                relevant_lines = []
                for i, line in enumerate(lines):
                    line_lower = line.lower()
                    line_original = line
                    # キーワードが含まれている行を検索
                    if any(keyword.lower() in line_lower or keyword in line_original for keyword in keywords):
                        # 前後の行も含める（コンテキスト）
                        start = max(0, i - 2)
                        end = min(len(lines), i + 3)
                        context = '\n'.join(lines[start:end])
                        relevant_lines.append({
                            'line': i + 1,
                            'content': context.strip(),
                            'match_line': i + 1
                        })
                
                if relevant_lines:
                    # 最も関連性の高い部分を選択（複数ある場合は最初の数個）
                    for match in relevant_lines[:2]:  # 各ドキュメントから最大2箇所
                        results.append({
                            'title': doc_data['name'],
                            'content': match['content'],
                            'line': match['line'],
                            'score': total_score
                        })
        
        # スコアでソート
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # 最大結果数まで返す
        return results[:max_results]
    
    def reload(self):
        """ドキュメントを再読み込み"""
        self.documents_cache = {}
        self._load_documents()

