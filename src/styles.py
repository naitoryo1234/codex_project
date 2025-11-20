def get_css() -> str:
    return """
    <style>
        /* --- 全体設定 --- */
        .stApp {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #121212; /* 完全な黒より少し明るいダークグレー */
            color: #e0e0e0;
        }
        
        /* スマホの余白を極限まで減らして画面を広く使う */
        .block-container {
            padding-top: 0.5rem !important;
            padding-bottom: 2rem !important;
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
            max-width: 100% !important;
        }

        /* --- タイトル --- */
        h1 {
            font-size: 1.4rem !important;
            font-weight: 700 !important;
            text-align: center;
            margin: 0 0 0.8rem 0 !important;
            padding: 0.5rem 0;
            background: linear-gradient(90deg, #3498db, #2ecc71);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            border-bottom: 1px solid #333;
        }

        /* --- カウンターエリア --- */
        .counter-area {
            background-color: #1e1e1e;
            border-radius: 12px;
            padding: 10px;
            margin-bottom: 15px;
            text-align: center;
            border: 1px solid #333;
        }
        .counter-label {
            font-size: 0.85rem;
            color: #aaa;
            margin-bottom: 5px;
        }

        /* --- ボタンのスタイル強化 (スマホで押しやすく) --- */
        div[data-testid="stButton"] button {
            width: 100%;
            border-radius: 8px;
            height: 3rem; /* 高さ確保 */
            font-weight: bold;
            border: none;
            background-color: #2c3e50;
            color: white;
            transition: background 0.2s;
        }
        div[data-testid="stButton"] button:active {
            background-color: #1abc9c;
            transform: scale(0.98);
        }
        /* プライマリボタン（判別ボタンなど） */
        div[data-testid="stButton"] button[kind="primary"] {
            background-color: #2980b9;
        }

        /* --- 結果カード --- */
        .info-card {
            background-color: #1e1e1e;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            border: 1px solid #333;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        
        .result-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
            font-size: 0.95rem;
            color: #bbb;
            font-weight: 600;
        }
        
        .result-card-value {
            font-size: 2.2rem; /* 数値を大きく */
            font-weight: 800;
            color: #fff;
            line-height: 1.1;
            margin-bottom: 4px;
            font-variant-numeric: tabular-nums;
        }
        
        .result-card-sub {
            font-size: 0.85rem;
            color: #888;
        }

        /* --- 星評価 --- */
        .star-rating {
            font-size: 1.4rem;
            letter-spacing: 1px;
        }
        .star-on { color: #f1c40f; text-shadow: 0 0 8px rgba(241, 196, 15, 0.6); }
        .star-off { color: #444; }

        /* --- アドバイスボックス --- */
        .advice-box {
            margin-top: 12px;
            padding: 12px;
            background-color: #252525;
            border-radius: 8px;
            border-left: 5px solid #3498db;
            font-size: 0.9rem;
            line-height: 1.6;
            color: #ddd;
        }
        .advice-box.high { border-color: #e74c3c; background-color: #2c2020; }
        .advice-box.low { border-color: #7f8c8d; }

        /* --- プログレスバー --- */
        .bar-wrapper {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }
        .bar-label {
            width: 45px;
            font-size: 0.85rem;
            font-weight: bold;
            color: #ccc;
        }
        .bar-track {
            flex: 1;
            height: 12px; /* 太くして見やすく */
            background-color: #333;
            border-radius: 6px;
            overflow: hidden;
            margin: 0 10px;
        }
        .bar-fill {
            height: 100%;
            border-radius: 6px;
        }
        .bar-value {
            width: 50px;
            text-align: right;
            font-size: 0.9rem;
            font-weight: bold;
            color: #fff;
        }

        /* --- 設定別カラー --- */
        .bg-1 { background-color: #95a5a6; }
        .bg-2 { background-color: #7f8c8d; }
        .bg-4 { background-color: #f1c40f; }
        .bg-5 { background-color: #e67e22; }
        .bg-6 { background: linear-gradient(90deg, #e74c3c, #c0392b); }

        /* --- 入力フォーム調整 --- */
        /* ラベルを少し大きく */
        label {
            font-size: 0.9rem !important;
            color: #ccc !important;
        }
        /* 入力ボックス */
        .stNumberInput input {
            font-size: 1.1rem;
            padding: 0.5rem;
        }
    </style>
    """
