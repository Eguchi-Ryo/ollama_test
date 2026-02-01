// 現在の機能タイプ
let currentFunctionType = 'chatbot';

// 機能の説明
const functionDescriptions = {
    chatbot: '社内文書を参照しながら質問にお答えします',
    daily_report: '音声入力や設備データを日報フォーマットに変換します',
    anomaly_detection: 'マルチモーダルな入力データから異常を検知します',
    production_plan: '様々な情報から動的な生産計画を生成します'
};

// 機能のタイトル
const functionTitles = {
    chatbot: 'チャットボット',
    daily_report: '日報生成',
    anomaly_detection: '異常検知',
    production_plan: '生産計画'
};

// DOM要素の取得
const menuButtons = document.querySelectorAll('.menu-btn');
const functionTitle = document.getElementById('functionTitle');
const functionDescription = document.getElementById('functionDescription');
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const documentList = document.getElementById('documentList');
const sourcesContainer = document.getElementById('sourcesContainer');
const fileInput = document.getElementById('fileInput');
const uploadBtn = document.getElementById('uploadBtn');

// メニューボタンのイベントリスナー
menuButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        // アクティブ状態の切り替え
        menuButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // 機能タイプの更新
        currentFunctionType = btn.dataset.function;
        
        // タイトルと説明の更新
        functionTitle.textContent = functionTitles[currentFunctionType];
        functionDescription.textContent = functionDescriptions[currentFunctionType];
        
        // チャット履歴をクリア（オプション）
        // chatMessages.innerHTML = '';
        
        // プレースホルダーの更新
        updatePlaceholder();
    });
});

// プレースホルダーの更新
function updatePlaceholder() {
    const placeholders = {
        chatbot: '質問を入力してください...',
        daily_report: '音声入力や設備データを入力してください...',
        anomaly_detection: '分析したいデータを入力してください...',
        production_plan: '生産計画に必要な情報を入力してください...'
    };
    chatInput.placeholder = placeholders[currentFunctionType] || 'メッセージを入力してください...';
}

// 送信ボタンのイベントリスナー
sendBtn.addEventListener('click', sendMessage);

// Enterキーで送信（Shift+Enterで改行）
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// メッセージ送信関数
async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message) return;
    
    // ユーザーメッセージを表示
    addMessage(message, 'user');
    chatInput.value = '';
    sendBtn.disabled = true;
    
    // ローディングメッセージを表示
    const loadingId = addMessage('考え中...', 'bot', true);
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                function_type: currentFunctionType
            })
        });
        
        const data = await response.json();
        
        // ローディングメッセージを削除
        removeMessage(loadingId);
        
        if (data.success) {
            // ボットの応答を表示
            addMessage(data.response, 'bot');
            
            // 参照元を表示
            if (data.sources && data.sources.length > 0) {
                displaySources(data.sources);
            }
        } else {
            addMessage('エラーが発生しました: ' + (data.error || '不明なエラー'), 'bot');
        }
    } catch (error) {
        removeMessage(loadingId);
        addMessage('通信エラーが発生しました: ' + error.message, 'bot');
    } finally {
        sendBtn.disabled = false;
    }
}

// メッセージを追加
function addMessage(content, type, isTemporary = false) {
    const messageDiv = document.createElement('div');
    const id = isTemporary ? 'temp-' + Date.now() : null;
    if (id) messageDiv.id = id;
    messageDiv.className = `message ${type}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    // スクロールを最下部に
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return id;
}

// メッセージを削除（一時メッセージ用）
function removeMessage(id) {
    const message = document.getElementById(id);
    if (message) {
        message.remove();
    }
}

// 参照元を表示
function displaySources(sources) {
    sourcesContainer.innerHTML = '';
    
    if (sources.length === 0) {
        sourcesContainer.innerHTML = '<p class="no-sources">現在、参照元はありません</p>';
        return;
    }
    
    sources.forEach(source => {
        const sourceDiv = document.createElement('div');
        sourceDiv.className = 'source-item';
        
        const title = document.createElement('h4');
        title.textContent = source.title || '参照元';
        
        const content = document.createElement('p');
        content.textContent = source.content || source;
        
        sourceDiv.appendChild(title);
        sourceDiv.appendChild(content);
        sourcesContainer.appendChild(sourceDiv);
    });
}

// ドキュメント一覧を読み込み
async function loadDocuments() {
    try {
        const response = await fetch('/api/documents');
        const data = await response.json();
        
        documentList.innerHTML = '';
        
        if (data.documents && data.documents.length > 0) {
            data.documents.forEach(doc => {
                const docDiv = document.createElement('div');
                docDiv.className = 'document-item';
                docDiv.textContent = doc.name;
                docDiv.addEventListener('click', () => {
                    document.querySelectorAll('.document-item').forEach(item => {
                        item.classList.remove('selected');
                    });
                    docDiv.classList.add('selected');
                });
                documentList.appendChild(docDiv);
            });
        } else {
            documentList.innerHTML = '<p class="no-sources">ドキュメントがありません</p>';
        }
    } catch (error) {
        documentList.innerHTML = '<p class="no-sources">ドキュメントの読み込みに失敗しました</p>';
    }
}

// ファイルアップロード
uploadBtn.addEventListener('click', () => {
    const files = fileInput.files;
    if (files.length === 0) {
        alert('ファイルを選択してください');
        return;
    }
    
    // デモ用：実際のアップロード機能は実装していません
    alert(`${files.length}個のファイルが選択されました（デモモード）`);
    fileInput.value = '';
});

// 初期化
document.addEventListener('DOMContentLoaded', () => {
    loadDocuments();
    updatePlaceholder();
});

