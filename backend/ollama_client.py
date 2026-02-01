import subprocess
import json
import os
import requests

class OllamaClient:
    def __init__(self, ollama_path):
        self.ollama_path = ollama_path
        self.model = "tinyllama"  # 軽量モデル（約637MB）
        self.api_url = "http://localhost:11434/api/generate"  # OllamaのデフォルトAPI URL
        self.list_url = "http://localhost:11434/api/tags"  # モデル一覧取得API
        
    def _run_ollama(self, prompt, system_prompt=None):
        """Ollamaを実行してレスポンスを取得"""
        try:
            # まずHTTP APIを試す
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 500  # 最大トークン数を制限して高速化
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            response = requests.post(self.api_url, json=payload, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                # APIが利用できない場合はコマンドラインを試す
                full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
                return self._run_ollama_cli(full_prompt)
        except (requests.exceptions.RequestException, Exception) as e:
            print(f"Ollama APIエラー: {e}")
            # フォールバック: コマンドライン実行
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            return self._run_ollama_cli(full_prompt)
    
    def _run_ollama_cli(self, prompt):
        """コマンドライン経由でOllamaを実行（フォールバック）"""
        try:
            cmd = [
                self.ollama_path,
                "run",
                self.model,
                prompt
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return self._get_demo_response(prompt)
        except Exception as e:
            print(f"Ollama CLI実行エラー: {e}")
            return self._get_demo_response(prompt)
    
    def _get_demo_response(self, prompt):
        """デモ用のフォールバックレスポンス"""
        return f"デモモード: あなたの質問「{prompt}」を受け取りました。実際のOllamaモデルが利用可能になると、より詳細な回答が提供されます。"
    
    def list_models(self):
        """インストール済みモデル一覧を取得"""
        try:
            # HTTP APIで取得を試みる
            response = requests.get(self.list_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = [model.get('name', '').split(':')[0] for model in data.get('models', [])]
                return list(set(models))  # 重複を除去
        except Exception as e:
            print(f"モデル一覧取得エラー（API）: {e}")
        
        # フォールバック: コマンドラインで取得
        try:
            cmd = [self.ollama_path, "list"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # ヘッダーをスキップ
                models = []
                for line in lines:
                    if line.strip():
                        model_name = line.split()[0].split(':')[0]
                        models.append(model_name)
                return list(set(models))
        except Exception as e:
            print(f"モデル一覧取得エラー（CLI）: {e}")
        
        return []
    
    def model_exists(self, model_name):
        """指定されたモデルがインストールされているか確認"""
        models = self.list_models()
        return model_name in models
    
    def download_model(self, model_name):
        """モデルをダウンロード"""
        print(f"\nモデル '{model_name}' をダウンロードしています...")
        print("（初回ダウンロードには数分かかる場合があります）\n")
        try:
            # HTTP APIでダウンロードを試みる
            pull_url = "http://localhost:11434/api/pull"
            payload = {"name": model_name}
            response = requests.post(pull_url, json=payload, stream=True, timeout=600)
            
            if response.status_code == 200:
                # ストリーミングレスポンスを処理
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if 'status' in data:
                                status = data['status']
                                # 進捗情報を表示
                                if 'completed' in data and 'total' in data:
                                    completed = data.get('completed', 0)
                                    total = data.get('total', 0)
                                    if total > 0:
                                        percent = (completed / total) * 100
                                        print(f"  進捗: {percent:.1f}% ({completed}/{total}) - {status}")
                                    else:
                                        print(f"  {status}")
                                else:
                                    print(f"  {status}")
                        except json.JSONDecodeError:
                            pass
                print(f"\n✓ モデル '{model_name}' のダウンロードが完了しました。\n")
                return True
        except requests.exceptions.Timeout:
            print(f"タイムアウト: モデルダウンロードに時間がかかりすぎています。")
            return False
        except Exception as e:
            print(f"モデルダウンロードエラー（API）: {e}")
        
        # フォールバック: コマンドラインでダウンロード
        print("コマンドライン経由でダウンロードを試みます...")
        try:
            cmd = [self.ollama_path, "pull", model_name]
            # リアルタイムで出力を表示
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            for line in process.stdout:
                print(f"  {line.strip()}")
            
            process.wait()
            if process.returncode == 0:
                print(f"\n✓ モデル '{model_name}' のダウンロードが完了しました。\n")
                return True
            else:
                print(f"モデルダウンロードエラー: リターンコード {process.returncode}")
                return False
        except subprocess.TimeoutExpired:
            print(f"タイムアウト: モデルダウンロードに時間がかかりすぎています。")
            return False
        except Exception as e:
            print(f"モデルダウンロードエラー（CLI）: {e}")
            return False
    
    def check_ollama_running(self):
        """Ollamaが起動しているか確認"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def ensure_model(self):
        """モデルが存在することを確認し、なければダウンロード"""
        # Ollamaが起動しているか確認
        if not self.check_ollama_running():
            print("警告: Ollamaが起動していないようです。")
            print("Ollamaを起動してから再度お試しください。")
            print(f"起動コマンド: \"{self.ollama_path}\" serve")
            return False
        
        if self.model_exists(self.model):
            print(f"✓ モデル '{self.model}' は既にインストールされています。")
            print("  （次回以降も自動的に使用されます）")
            return True
        
        print(f"モデル '{self.model}' が見つかりません。ダウンロードを開始します...")
        print("  ※ 初回のみダウンロードが必要です。次回以降は自動的に使用されます。")
        return self.download_model(self.model)
    
    def chat(self, message):
        """チャットボット機能"""
        system_prompt = "あなたは製造現場の熟練作業員のノウハウを継承するAIアシスタントです。社内ドキュメントを参照しながら、質問に答えてください。必ず日本語で回答してください。"
        prompt = f"質問: {message}\n\n回答（日本語で）:"
        return self._run_ollama(prompt, system_prompt)
    
    def generate_daily_report(self, input_data):
        """日報生成機能"""
        system_prompt = "あなたは製造現場の日報を作成するアシスタントです。提供された音声入力や設備データを基に、日報フォーマットに整理してください。必ず日本語で回答してください。"
        prompt = f"入力データ: {input_data}\n\n日報（日本語で）:"
        return self._run_ollama(prompt, system_prompt)
    
    def detect_anomaly(self, input_data):
        """異常検知機能"""
        system_prompt = "あなたは製造現場の異常検知システムです。提供されたマルチモーダルな入力データ（画像、センサーデータなど）を分析し、通常と異なる状態を発見してください。必ず日本語で回答してください。"
        prompt = f"入力データ: {input_data}\n\n分析結果（日本語で）:"
        return self._run_ollama(prompt, system_prompt)
    
    def generate_production_plan(self, input_data):
        """生産計画生成機能"""
        system_prompt = "あなたは製造現場の生産計画を動的に生成するアシスタントです。組立員のシフト、部材の仕入れ状況、設備の稼働状況などの情報を基に、最適な生産計画を提案してください。必ず日本語で回答してください。"
        prompt = f"入力情報: {input_data}\n\n生産計画（日本語で）:"
        return self._run_ollama(prompt, system_prompt)

