import math
from typing import Dict, List, Any
from .constants import SETTINGS, SETTING_KEYS, GOAL_CONFIG

def calculate_likelihood(num_spins: int, num_hits: int, p: float) -> float:
    """二項分布の尤度 P(K=k | N=n, p)"""
    if p <= 0.0 or p >= 1.0 or num_spins <= 0 or num_hits < 0 or num_hits > num_spins:
        return 0.0
    log_nCk = (
        math.lgamma(num_spins + 1)
        - math.lgamma(num_hits + 1)
        - math.lgamma(num_spins - num_hits + 1)
    )
    log_likelihood = (
        log_nCk
        + num_hits * math.log(p)
        + (num_spins - num_hits) * math.log(1.0 - p)
    )
    return math.exp(log_likelihood)

def normalize(priors: Dict[str, float]) -> Dict[str, float]:
    """確率分布の正規化"""
    total = sum(max(0.0, priors.get(k, 0.0)) for k in SETTING_KEYS)
    if total <= 0.0:
        uniform = 1.0 / len(SETTING_KEYS)
        return {k: uniform for k in SETTING_KEYS}
    return {k: max(0.0, priors.get(k, 0.0)) / total for k in SETTING_KEYS}

def compute_posteriors(num_spins: int, num_hits: int, priors: Dict[str, float]) -> Dict[str, float]:
    """ベイズ更新による事後確率計算"""
    priors = normalize(priors)
    posterior_numerators: Dict[str, float] = {}
    marginal_likelihood = 0.0
    
    for key in SETTING_KEYS:
        p = SETTINGS[key]
        prior = priors.get(key, 0.0)
        likelihood = calculate_likelihood(num_spins, num_hits, p) if prior > 0.0 else 0.0
        numerator = likelihood * prior
        posterior_numerators[key] = numerator
        marginal_likelihood += numerator
        
    if marginal_likelihood > 0.0:
        return {k: posterior_numerators[k] / marginal_likelihood for k in SETTING_KEYS}
    return priors

def evaluate_goal(goal_code: str, goal_prob: float, alt_prob: float, sample_n: int, ci_range_pct: float) -> Dict[str, Any]:
    """
    設定判別の信頼度を評価し、状況に応じた詳細なコメントを生成する
    """
    config = GOAL_CONFIG[goal_code]
    
    # 確率比と差
    alt_prob_safe = max(alt_prob, 1e-9)
    ratio = goal_prob / alt_prob_safe if alt_prob_safe > 0 else float("inf")
    diff_pct = (goal_prob - alt_prob) * 100.0
    goal_prob_pct = goal_prob * 100.0
    
    # 基本スコア計算
    score = 0
    thresholds_goal = config["goal_thresholds"]
    
    if goal_prob_pct >= thresholds_goal["high"]: score += 2
    elif goal_prob_pct >= thresholds_goal["mid"]: score += 1
    elif goal_prob_pct <= thresholds_goal["low"]: score -= 1
    
    diff_thresholds = config["diff_thresholds"]
    if diff_pct >= diff_thresholds["high"]: score += 2
    elif diff_pct >= diff_thresholds["mid"]: score += 1
    
    # 星の数決定 (暫定)
    if score >= 4: star = 5
    elif score >= 3: star = 4
    elif score >= 1: star = 3
    elif score >= -1: star = 2
    else: star = 1

    # --- コメント生成ロジックの強化 ---
    comment = ""
    
    # 1. サンプル数によるコンテキスト
    is_early = sample_n < 1000
    is_mid = 1000 <= sample_n < 3000
    is_late = sample_n >= 3000
    
    # 2. 状況別のコメント分岐
    if is_early:
        # 序盤の展開
        if star >= 4:
            comment = "🚀 最高のロケットスタート！サンプルは少ないですが、期待して良さそうです。"
        elif star == 3:
            comment = "🤔 まずまずの滑り出し。まだブレる時期なので、小役以外の要素も要チェック。"
        elif star <= 2:
            comment = "💦 出足は鈍いですが、まだ見切るには早すぎます。もう少し様子を見ましょう。"
            
    elif is_mid:
        # 中盤の展開
        if star == 5:
            comment = "✨ 高設定の挙動で安定しています。このまま自信を持って回しましょう！"
        elif star == 4:
            comment = "📈 かなり良い感触です。決定打（トロフィー等）が出れば安心できます。"
        elif star == 3:
            comment = "⚖️ どっちつかずの展開。ここからの1000Gが勝負の分かれ目になりそうです。"
        elif star == 2:
            comment = "☁️ 雲行きが怪しいです。他の強い根拠がなければ、撤退も視野に。"
        else:
            comment = "💀 低設定の可能性が高まってきました。深追いは禁物かもしれません。"
            
    else:
        # 終盤の展開
        if star >= 4:
            comment = "🏆 文句なしの高設定挙動！閉店までブン回し確定レベルです。"
        elif star == 3:
            comment = "🌀 最後まで悩みそうな数値です。自分の台の挙動とホールの状況を信じて判断を。"
        else:
            comment = "⛔ 残念ながら高設定の望みは薄そうです。無理せず切り上げるのが賢明です。"

    # 3. 特殊ケースの上書き・追記
    
    # 極端な上振れ (サンプル少なくても確率が異常に良い)
    # 例: 設定6の確率(1/22.5)を大きく上回る場合など
    # ここでは簡易的に goal_prob が極端に高い場合で判定
    if is_early and goal_prob_pct > 90.0:
        comment = "🔥 驚異的な引き！サンプル不足を補って余りある数値です。全ツッパの構えで！"
        star = 5 # 強制的に星5にする
        
    # サンプル不足だが可能性はある場合
    if sample_n < config["min_sample_warn"] and star <= 3 and goal_prob_pct > 40:
        comment += " (※まだ試行回数が少ないため、数値は大きく変動する可能性があります)"

    # 456だけど56は弱い場合 (設定4濃厚)
    if goal_code == "56" and star <= 2 and goal_prob_pct < 20 and alt_prob > 50:
        # これは呼び出し元で判定した方が正確だが、ここでも簡易的に
        pass 

    return {
        "stars": star,
        "comment": comment,
        "diff_pct": diff_pct,
        "ratio": ratio,
        "insufficient": sample_n < config["min_sample_warn"]
    }

def format_percent(prob: float) -> str:
    return f"{prob * 100.0:.1f}%"

def format_denominator(prob: float) -> str:
    if prob <= 0: return "0"
    inv = 1.0 / prob
    return f"1/{inv:.1f}"
