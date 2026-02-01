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
        
        # クエリをキーワードに分割（日本語も含む）
        # 日本語文字列も検出できるように改善
        keywords = []
        # 英数字の単語
        keywords.extend(re.findall(r'\w+', query.lower()))
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
          