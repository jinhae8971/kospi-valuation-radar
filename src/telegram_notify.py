"""
KOSPI Valuation Radar - 한국어 텔레그램 알림
- 섹터별 TOP 5 저평가 (Value 기준)
- Multi-Factor Long-Short TOP 5
- Regime + Factor Weights
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "docs" / "data" / "latest.json"

KST = timezone(timedelta(hours=9))
PAGES_URL_DEFAULT = "https://jinhae8971.github.io/kospi-valuation-radar/"

# 한글명 매핑
sys.path.insert(0, str(Path(__file__).parent))
from kr_names import get_kr_name, get_short_ticker


def load_config() -> Dict[str, str]:
    cfg = {
        "telegram_token":   os.environ.get("TELEGRAM_TOKEN",   ""),
        "telegram_chat_id": os.environ.get("TELEGRAM_CHAT_ID", ""),
        "pages_url":        os.environ.get("PAGES_URL", PAGES_URL_DEFAULT),
    }
    config_path = ROOT / "config.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            for k, v in json.load(f).items():
                if not cfg.get(k):
                    cfg[k] = v
    return cfg


def send_telegram(message: str, token: str, chat_id: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=20,
    )
    r.raise_for_status()


def format_number(v, fmt: str = ".1f") -> str:
    if v is None:
        return "N/A"
    try:
        return format(float(v), fmt)
    except (TypeError, ValueError):
        return "N/A"


def shorten_name(name: str, ticker: str = "", max_len: int = 14) -> str:
    """한국 종목명을 짧게 (영어/한글 혼용)"""
    if not name:
        # ticker만 표시
        return ticker.replace(".KS", "").replace(".KQ", "")
    n = name.strip()
    # 자주 등장하는 불필요한 접미사 제거
    for suffix in [" Co., Ltd.", " Co.,Ltd", " Corporation", " Inc.", " Corp.",
                   " CO.,LTD.", "(주)"]:
        n = n.replace(suffix, "")
    if len(n) > max_len:
        n = n[:max_len] + "…"
    return n


def build_message(snapshot: Dict[str, Any], top_n: int = 5) -> str:
    cfg = load_config()
    pages_url = cfg.get("pages_url", PAGES_URL_DEFAULT)

    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")

    lines: List[str] = []
    lines.append("🇰🇷 <b>KOSPI Valuation Radar</b>")
    lines.append(f"🕐 {now}")
    lines.append(f"📈 Universe: {snapshot['universe_size']} 종목 (KOSPI200+KOSDAQ)")

    # === Multi-factor + Regime ===
    mf_path = ROOT / "docs" / "data" / "multifactor.json"
    if mf_path.exists():
        try:
            with open(mf_path, "r", encoding="utf-8") as f:
                mf = json.load(f)
            regime = mf.get("regime", {})
            weights = mf.get("factor_weights", {})
            portfolio = mf.get("portfolio", {})

            lines.append("")
            lines.append("━━━━━━━━━━━━━━━━━━")
            lines.append("<b>🌐 Regime + Factor 가중치</b>")
            if regime.get("ai_semi_phase"):
                lines.append(f"  AI/반도체: <b>{regime['ai_semi_phase']}</b> ({regime.get('ai_semi_score', 0):.1f})")
            if regime.get("crypto_phase"):
                lines.append(f"  Crypto: <b>{regime['crypto_phase']}</b>")
            if regime.get("risk_regime"):
                lines.append(f"  종합: <b>{regime['risk_regime']}</b>")
            if regime.get("kospi_strategy_signal"):
                lines.append(f"  KOSPI 전략: <b>{regime['kospi_strategy_signal']}</b>")
            if weights:
                lines.append(
                    f"  Weights: V <b>{weights.get('value',0):.0%}</b> · "
                    f"Q <b>{weights.get('quality',0):.0%}</b> · "
                    f"M <b>{weights.get('momentum',0):.0%}</b>"
                )

            # Long-Short 상위 5
            if portfolio.get("positions"):
                longs = [p for p in portfolio["positions"] if p["side"] == "LONG"][:5]
                shorts = [p for p in portfolio["positions"] if p["side"] == "SHORT"][:5]
                lines.append("")
                lines.append("━━━━━━━━━━━━━━━━━━")
                lines.append("<b>🎯 Multi-Factor Long-Short TOP 5</b>")
                lines.append("📈 <b>LONG (롱)</b>:")
                for i, p in enumerate(longs, 1):
                    tk = p['ticker']
                    short = get_short_ticker(tk)
                    name = get_kr_name(tk)
                    sec = p.get('sector', '')[:15]
                    lines.append(f"  {i}. <b>{short} {name}</b>")
                    lines.append(f"     Score {p['final_score']:+.3f}  ·  <i>{sec}</i>")
                lines.append("📉 <b>SHORT (숏)</b>:")
                for i, p in enumerate(shorts, 1):
                    tk = p['ticker']
                    short = get_short_ticker(tk)
                    name = get_kr_name(tk)
                    sec = p.get('sector', '')[:15]
                    lines.append(f"  {i}. <b>{short} {name}</b>")
                    lines.append(f"     Score {p['final_score']:+.3f}  ·  <i>{sec}</i>")
        except Exception as e:
            print(f"⚠️ multifactor 로드 실패: {e}")

    # === 섹터별 저평가 TOP 5 ===
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━")
    lines.append("<b>💎 섹터별 저평가 TOP 5</b>")
    lines.append("<i>(Composite Z-score, 낮을수록 저평가)</i>")

    stocks_with_z = [
        s for s in snapshot["stocks"]
        if s.get("composite_z") is not None and s.get("super_sector")
    ]
    sectors = {}
    for s in stocks_with_z:
        sec = s["super_sector"]
        sectors.setdefault(sec, []).append(s)

    for sec, stocks in sectors.items():
        stocks.sort(key=lambda x: x["composite_z"])

    for sec in sorted(sectors.keys()):
        stocks = sectors[sec][:top_n]
        if not stocks:
            continue
        lines.append("")
        lines.append(f"🏷️ <b>{sec}</b>")
        for i, s in enumerate(stocks, 1):
            tk = s.get("ticker", "?")
            short = get_short_ticker(tk)
            name = get_kr_name(tk)
            z = s.get("composite_z")
            pe = s.get("pe")
            pb = s.get("pb")
            quality = s.get("quality_z")

            if quality is not None and quality > 0:
                q_marker = "✨"
            elif quality is not None and quality < -1:
                q_marker = "⚠️"
            else:
                q_marker = "  "

            lines.append(
                f"  {i}. {q_marker}<b>{short} {name}</b>\n"
                f"     Z=<b>{format_number(z, '+.2f')}</b> · "
                f"PE={format_number(pe, '.1f')} · "
                f"PB={format_number(pb, '.1f')}"
            )

    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━")
    lines.append("✨ 우량  ⚠️ 가치함정 주의")
    lines.append(f"🔗 <a href='{pages_url}'>전체 대시보드</a>")

    return "\n".join(lines)


def main():
    cfg = load_config()
    token = cfg.get("telegram_token", "")
    chat_id = cfg.get("telegram_chat_id", "")

    if not DATA_PATH.exists():
        print(f"❌ {DATA_PATH} 없음")
        sys.exit(1)

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        snapshot = json.load(f)

    msg = build_message(snapshot)

    if not token or not chat_id:
        print("⚠️ TELEGRAM 미설정 — 미리보기만 출력")
        print("\n--- 발송 예정 메시지 ---")
        print(msg)
        return

    print(f"발송 메시지: {len(msg)} chars")

    # 4000자 넘으면 분할
    if len(msg) > 4000:
        parts = msg.split("━━━━━━━━━━━━━━━━━━")
        current = ""
        for p in parts:
            if len(current) + len(p) > 3500:
                send_telegram(current, token, chat_id)
                current = p
            else:
                current += "━━━━━━━━━━━━━━━━━━" + p
        if current:
            send_telegram(current, token, chat_id)
    else:
        send_telegram(msg, token, chat_id)

    print("✓ Telegram 발송 완료")


if __name__ == "__main__":
    main()
