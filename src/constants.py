from typing import Dict, List

# 設定ごとの5枚役当選確率
# 1: 1/38.15, 2: 1/36.86, 4: 1/30.27, 5: 1/24.51, 6: 1/22.53
SETTINGS: Dict[str, float] = {
    "1": 1 / 38.15,
    "2": 1 / 36.86,
    "4": 1 / 30.27,
    "5": 1 / 24.51,
    "6": 1 / 22.53,
}

SETTING_KEYS: List[str] = list(SETTINGS.keys())

# 信頼度判定のための閾値設定
# 456: 設定4以上である確率
# 56: 設定5以上である確率
GOAL_CONFIG = {
    "456": {
        "min_sample_warn": 120,
        "min_sample_good": 220,
        "goal_thresholds": {"high": 75.0, "mid": 65.0, "low": 48.0},
        "diff_thresholds": {"high": 15.0, "mid": 7.0},
        "comments": {
            "insufficient": "サンプル不足です。まずはデータを集めましょう。",
            "very_low": "低設定の可能性が高いです。",
            "low": "456の可能性はまだ低いです。",
            "mid": "456のチャンスがあります。",
            "high": "456濃厚です！",
            "very_high": "456確信レベルです！",
        },
    },
    "56": {
        "min_sample_warn": 160,
        "min_sample_good": 240,
        "goal_thresholds": {"high": 58.0, "mid": 50.0, "low": 35.0},
        "diff_thresholds": {"high": 8.0, "mid": 4.0},
        "comments": {
            "insufficient": "サンプル不足です。",
            "very_low": "56は厳しそうです。",
            "low": "56狙いは慎重に。",
            "mid": "56の可能性アリ。設定4との判別が必要。",
            "high": "56にかなり期待できます。",
            "very_high": "56本命です！",
        },
    },
}
