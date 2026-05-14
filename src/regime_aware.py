"""
KOSPI Regime Awareness - 한국 시장 특화

기존 Younggil 시스템 활용:
- kospi-strategy:             일일 KOSPI 전략 (21:00 KST)
- ai-semi-cycle-intelligence: AI/반도체 사이클 (한국 반도체 종목이 유니버스 핵심)
- crypto-cycle-intelligence:  CCS (글로벌 유동성 참고용)

한국 시장 특수성:
- 미국 시장 영향이 절대적 (S&P500 / SOX 강한 동조)
- 환율(USD/KRW) 영향 큼 → 1320 이상이면 외국인 매도 압력
- 반도체 비중이 KOSPI에서 30%+ → ai-semi-cycle이 가장 중요한 시그널
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
import requests


REGIME_SOURCES = {
    "kospi_strategy":  "https://jinhae8971.github.io/kospi-strategy/data/latest.json",
    "ai_semi":         "https://jinhae8971.github.io/ai-semi-cycle-intelligence/data/latest.json",
    "crypto":          "https://jinhae8971.github.io/crypto-cycle-intelligence/data/latest.json",
}


@dataclass
class RegimeSnapshot:
    market: str = "KOSPI"
    # ai-semi (한국 반도체 사이클)
    ai_semi_phase: Optional[str] = None
    ai_semi_score: Optional[float] = None
    # 한국 strategy 자체 시그널
    kospi_strategy_signal: Optional[str] = None
    kospi_strategy_score: Optional[float] = None
    # 글로벌 유동성 참고
    crypto_phase: Optional[str] = None
    # 종합
    risk_regime: Optional[str] = None
    raw: Dict[str, Any] = None

    def to_dict(self):
        return asdict(self)


def _safe_fetch(url: str, timeout: int = 15) -> Optional[Dict[str, Any]]:
    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"  [regime fetch warn] {url[:60]}... → {e}")
    return None


def fetch_regime() -> RegimeSnapshot:
    raw: Dict[str, Any] = {}

    # ai-semi
    ai_semi_phase, ai_semi_score = None, None
    aisem = _safe_fetch(REGIME_SOURCES["ai_semi"])
    if aisem:
        raw["ai_semi_generated_at"] = aisem.get("generated_at")
        ascs = aisem.get("ascs") or {}
        ai_semi_phase = ascs.get("phase")
        comp = ascs.get("composite")
        if isinstance(comp, (int, float)):
            ai_semi_score = float(comp)

    # KOSPI strategy
    kospi_signal, kospi_score = None, None
    ks = _safe_fetch(REGIME_SOURCES["kospi_strategy"])
    if ks:
        raw["kospi_strategy_generated_at"] = ks.get("generated_at")
        # 다양한 키 시도 (실제 구조 불확실)
        for key in ("signal", "regime", "strategy", "recommendation", "stance"):
            if key in ks:
                kospi_signal = str(ks[key])
                break
        for key in ("score", "kospi_score", "composite_score"):
            if key in ks:
                try: kospi_score = float(ks[key])
                except (TypeError, ValueError): pass
                break

    # crypto
    crypto_phase = None
    cc = _safe_fetch(REGIME_SOURCES["crypto"])
    if cc:
        ccs = cc.get("ccs") or {}
        crypto_phase = ccs.get("phase")

    # 종합 risk_regime 산출 (ai-semi가 한국 시장에 가장 중요)
    risk_regime = None
    if ai_semi_score is not None:
        if ai_semi_score > 75:
            risk_regime = "Late Bull (한국 반도체 과열)"
        elif ai_semi_score > 50:
            risk_regime = "RiskOn"
        elif ai_semi_score > 30:
            risk_regime = "Neutral"
        else:
            risk_regime = "RiskOff"

    return RegimeSnapshot(
        market="KOSPI",
        ai_semi_phase=ai_semi_phase,
        ai_semi_score=ai_semi_score,
        kospi_strategy_signal=kospi_signal,
        kospi_strategy_score=kospi_score,
        crypto_phase=crypto_phase,
        risk_regime=risk_regime,
        raw=raw,
    )


def get_factor_weights(regime: RegimeSnapshot) -> Dict[str, float]:
    """
    한국 시장 특화 factor weights.
    
    한국 특수성 반영:
    - 한국은 Value factor가 더 잘 작동 (Korea Discount 해소 베팅)
    - Momentum은 미국보다 약함 (개미 추격매수 + 외국인 회전)
    - Quality는 재무 투명성 이슈로 더 중요
    """
    phase = (regime.ai_semi_phase or "").lower()

    if "deep bottom" in phase or "bottom" in phase:
        # 한국 바닥에서는 Value가 극단적으로 강력
        return {"value": 0.60, "quality": 0.30, "momentum": 0.10}
    elif "accumulation" in phase or "early" in phase:
        return {"value": 0.50, "quality": 0.30, "momentum": 0.20}
    elif "mid" in phase or "expansion" in phase:
        return {"value": 0.40, "quality": 0.25, "momentum": 0.35}
    elif "late bull" in phase or "late" in phase:
        # 한국 후기 사이클은 더 방어적 (외국인 매도 위험)
        return {"value": 0.30, "quality": 0.50, "momentum": 0.20}
    elif "distribution" in phase or "top" in phase:
        return {"value": 0.25, "quality": 0.60, "momentum": 0.15}

    # Fallback
    return {"value": 0.45, "quality": 0.35, "momentum": 0.20}


if __name__ == "__main__":
    snap = fetch_regime()
    print("=== KOSPI Regime Snapshot ===")
    print(f"  AI/Semi:        {snap.ai_semi_phase} (score: {snap.ai_semi_score})")
    print(f"  KOSPI Strategy: {snap.kospi_strategy_signal} (score: {snap.kospi_strategy_score})")
    print(f"  Crypto:         {snap.crypto_phase}")
    print(f"  Risk Regime:    {snap.risk_regime}")
    print()
    w = get_factor_weights(snap)
    print("=== Factor Weights (Korea-specific) ===")
    for k, v in w.items():
        print(f"  {k.capitalize():10s}: {v:.0%}")
