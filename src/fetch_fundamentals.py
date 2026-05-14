"""
KOSPI Valuation Radar - Fundamentals fetcher

⚠️ 미국 버전과의 핵심 차이점:
1. yfinance 한국 종목은 trailingPE / priceToBook 직접 제공 안 함
   → financials + balance_sheet 로 직접 계산
2. KRW 통화 (price * shares = market_cap)
3. 한국 시장 멀티플은 미국보다 낮음 (Korea Discount):
   - P/E 5~25, P/B 0.5~5 가 일반적
   - 이상치 범위를 미국과 다르게 설정
4. forwardPE 는 사용 가능 → 보조 지표로 활용
5. PEG ratio 도 일부 제공 → 보조 지표

Z-score 계산은 미국과 동일 (super-sector별 Robust)
"""
from __future__ import annotations

import json
import math
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

import pandas as pd
import numpy as np
import yfinance as yf

sys.path.insert(0, str(Path(__file__).parent))
from universe import (
    UNIVERSE, get_all_tickers, get_ticker_to_sector,
    get_ticker_to_super_sector, get_super_sector,
)


# ---------------------------------------------------------------------------
KST = timezone(timedelta(hours=9))
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "docs" / "data"
HISTORY_DIR = DATA_DIR / "history"


# 한국 시장 멀티플 허용 범위 (Korea Discount 반영, 미국보다 좁음)
METRIC_BOUNDS = {
    "pe":         (0.5,  300),    # P/E 0.5~300 (적자 제외)
    "ps":         (0.05, 50),     # P/S 0.05~50
    "pb":         (0.1,  30),     # P/B 0.1~30
    "ev_ebitda":  (1.0,  100),    # EV/EBITDA 1~100
    "ev_sales":   (0.1,  50),     # EV/Sales 0.1~50
    "forward_pe": (0.5,  200),    # Forward PE
    "peg":        (0.05, 10),     # PEG ratio
}


INFO_FIELDS = {
    "name":         "longName",
    "short_name":   "shortName",
    "price":        "currentPrice",
    "market_cap":   "marketCap",
    "currency":     "currency",
    "industry":     "industry",
    "sector_gics":  "sector",
    "shares":       "sharesOutstanding",
}

# yfinance가 직접 제공하는 멀티플 (한국주는 일부만)
DIRECT_METRIC_FIELDS = {
    "ps":         "priceToSalesTrailing12Months",
    "ev_ebitda":  "enterpriseToEbitda",
    "ev_sales":   "enterpriseToRevenue",
    "forward_pe": "forwardPE",
    "peg":        "pegRatio",
}

QUALITY_FIELDS = {
    "profit_margin":   "profitMargins",
    "roe":             "returnOnEquity",
    "revenue_growth":  "revenueGrowth",
    "gross_margin":    "grossMargins",
    "operating_margin":"operatingMargins",
}


# ---------------------------------------------------------------------------
def _safe_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def _bounded(v: Any, key: str) -> Optional[float]:
    f = _safe_float(v)
    if f is None:
        return None
    lo, hi = METRIC_BOUNDS.get(key, (None, None))
    if lo is not None and f < lo:
        return None
    if hi is not None and f > hi:
        return None
    return f


def _get(df: pd.DataFrame, candidates: List[str], col_idx: int = 0) -> Optional[float]:
    """DataFrame에서 후보 키 중 첫 번째 매치 값 추출"""
    if df is None or df.empty or col_idx >= len(df.columns):
        return None
    for cand in candidates:
        if cand in df.index:
            v = df.iloc[df.index.get_loc(cand), col_idx]
            if pd.isna(v):
                continue
            try:
                return float(v)
            except (TypeError, ValueError):
                continue
    return None


# ---------------------------------------------------------------------------
def fetch_ticker_data(ticker: str, retries: int = 2) -> Dict[str, Any]:
    """
    한국 종목 펀더멘털 수집.
    yfinance가 trailingPE / priceToBook 제공 안 하므로 직접 계산.
    """
    for attempt in range(retries + 1):
        try:
            t = yf.Ticker(ticker)
            info = t.info
            if not info or "symbol" not in info:
                if attempt < retries:
                    time.sleep(0.5)
                    continue
                return {"ticker": ticker, "error": "no_info"}

            row: Dict[str, Any] = {"ticker": ticker}
            for key, yf_field in INFO_FIELDS.items():
                row[key] = info.get(yf_field)

            # === 직접 제공되는 멀티플 ===
            for key, yf_field in DIRECT_METRIC_FIELDS.items():
                row[key] = _bounded(info.get(yf_field), key)

            # === Quality 지표 ===
            for key, yf_field in QUALITY_FIELDS.items():
                row[key] = _safe_float(info.get(yf_field))

            # === P/E, P/B 직접 계산 ===
            price = _safe_float(info.get("currentPrice"))
            market_cap = _safe_float(info.get("marketCap"))
            shares = _safe_float(info.get("sharesOutstanding"))

            # Trailing P/E = price / EPS = market_cap / net_income
            try:
                inc = t.financials  # annual
                bs  = t.balance_sheet
            except Exception:
                inc, bs = None, None

            net_income = _get(inc, ["Net Income", "Net Income Common Stockholders",
                                    "Net Income From Continuing Operation Net Minority Interest"], 0)
            equity = _get(bs, ["Common Stock Equity", "Stockholders Equity",
                              "Total Equity Gross Minority Interest"], 0)

            # P/E
            pe_calc = None
            if market_cap is not None and net_income is not None and net_income > 0:
                pe_calc = market_cap / net_income
            row["pe"] = _bounded(pe_calc, "pe")

            # P/B
            pb_calc = None
            if market_cap is not None and equity is not None and equity > 0:
                pb_calc = market_cap / equity
            row["pb"] = _bounded(pb_calc, "pb")

            # 추가 raw 값 (디버깅용)
            row["_net_income"] = net_income
            row["_equity"] = equity

            return row

        except Exception as e:
            if attempt < retries:
                time.sleep(1.0)
                continue
            return {"ticker": ticker, "error": str(e)[:200]}

    return {"ticker": ticker, "error": "exhausted_retries"}


def fetch_all(tickers: List[str], verbose: bool = True) -> pd.DataFrame:
    rows = []
    n = len(tickers)
    for i, t in enumerate(tickers, 1):
        if verbose:
            print(f"  [{i:3d}/{n}] {t:12s}", end="", flush=True)
        row = fetch_ticker_data(t)
        rows.append(row)
        if verbose:
            err = row.get("error")
            if err:
                print(f"  ERR: {err[:60]}")
            else:
                pe = row.get("pe")
                ps = row.get("ps")
                pb = row.get("pb")
                print(f"  PE={pe!s:>7} PS={ps!s:>7} PB={pb!s:>7}")
        time.sleep(0.2)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
def robust_zscore(series: pd.Series, winsorize_z: float = 5.0) -> pd.Series:
    """Robust Z-score with winsorization (미국 버전과 동일)"""
    s = series.dropna()
    if len(s) < 3:
        return pd.Series([np.nan] * len(series), index=series.index)
    med = s.median()
    mad = (s - med).abs().median()
    if mad == 0 or pd.isna(mad):
        return pd.Series([np.nan] * len(series), index=series.index)
    z = (series - med) / (1.4826 * mad)
    return z.clip(lower=-winsorize_z, upper=winsorize_z)


def compute_sector_zscores(
    df: pd.DataFrame,
    sector_col: str = "super_sector",
    min_sector_size: int = 5,
) -> pd.DataFrame:
    """섹터별 Robust Z-score (미국과 동일 로직)"""
    out = df.copy()
    z_cols = []

    sector_sizes = out.groupby(sector_col).size()
    valid_sectors = set(sector_sizes[sector_sizes >= min_sector_size].index)
    valid_mask = out[sector_col].isin(valid_sectors)

    # 5개 핵심 지표
    metrics = ["pe", "ps", "pb", "ev_ebitda", "ev_sales"]
    for metric in metrics:
        z_col = f"z_{metric}"
        z_cols.append(z_col)
        out[z_col] = np.nan
        if valid_mask.any():
            out.loc[valid_mask, z_col] = (
                out.loc[valid_mask]
                  .groupby(sector_col)[metric]
                  .transform(robust_zscore)
            )

    # Composite: 최소 3개 지표 필요
    MIN_METRICS = 3
    raw_mean = out[z_cols].mean(axis=1, skipna=True)
    n_metrics = out[z_cols].notna().sum(axis=1)
    out["composite_z"] = raw_mean.where(n_metrics >= MIN_METRICS, np.nan)
    out["z_count"] = n_metrics
    out["sector_n"] = out[sector_col].map(sector_sizes).astype("Int64")
    return out


def compute_quality_score(df: pd.DataFrame) -> pd.DataFrame:
    """Quality Z-score (전체 유니버스 기준)"""
    out = df.copy()
    quality_cols = []
    for metric in QUALITY_FIELDS.keys():
        z_col = f"q_{metric}"
        quality_cols.append(z_col)
        s = out[metric]
        med = s.median()
        mad = (s - med).abs().median()
        if mad and not pd.isna(mad) and mad > 0:
            out[z_col] = ((s - med) / (1.4826 * mad)).clip(-5, 5)
        else:
            out[z_col] = np.nan
    out["quality_z"] = out[quality_cols].mean(axis=1, skipna=True)
    return out


def assign_sectors(df: pd.DataFrame) -> pd.DataFrame:
    mapping = get_ticker_to_sector()
    super_mapping = get_ticker_to_super_sector()
    df = df.copy()
    df["sector"] = df["ticker"].map(mapping)
    df["super_sector"] = df["ticker"].map(super_mapping)
    return df


# ---------------------------------------------------------------------------
def build_snapshot(df: pd.DataFrame) -> Dict[str, Any]:
    now_kst = datetime.now(KST)

    super_sector_stats = []
    for sec in df["super_sector"].dropna().unique():
        sub = df[df["super_sector"] == sec]
        valid = sub.dropna(subset=["composite_z"])
        super_sector_stats.append({
            "super_sector": sec,
            "n_total": int(len(sub)),
            "n_valid": int(len(valid)),
            "median_pe":        _safe_float(sub["pe"].median()),
            "median_ps":        _safe_float(sub["ps"].median()),
            "median_pb":        _safe_float(sub["pb"].median()),
            "median_ev_ebitda": _safe_float(sub["ev_ebitda"].median()),
            "median_ev_sales":  _safe_float(sub["ev_sales"].median()),
            "tickers": sub["ticker"].tolist(),
        })

    sector_stats = []
    for sec in df["sector"].dropna().unique():
        sub = df[df["sector"] == sec]
        sector_stats.append({
            "sector": sec,
            "n_total": int(len(sub)),
            "tickers": sub["ticker"].tolist(),
        })

    stocks = []
    for _, row in df.iterrows():
        stock = {}
        for k, v in row.items():
            if k.startswith("_"):  # debug 필드 제외
                continue
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                stock[k] = None
            elif pd.isna(v):
                stock[k] = None
            elif isinstance(v, (np.integer, np.int64)):
                stock[k] = int(v)
            elif isinstance(v, (np.floating, np.float64)):
                stock[k] = float(v)
            else:
                stock[k] = v
        stocks.append(stock)

    return {
        "generated_at_kst": now_kst.strftime("%Y-%m-%d %H:%M:%S KST"),
        "generated_at_iso": now_kst.isoformat(),
        "market": "KOSPI/KOSDAQ",
        "currency": "KRW",
        "universe_size": len(df),
        "super_sectors": super_sector_stats,
        "sectors": sector_stats,
        "stocks": stocks,
    }


# ---------------------------------------------------------------------------
def main():
    print("=" * 72)
    print("KOSPI Valuation Radar — Fundamentals Fetch")
    print("=" * 72)

    tickers = get_all_tickers()
    print(f"Universe size: {len(tickers)}")

    df = fetch_all(tickers, verbose=True)
    print(f"\nFetched: {len(df)} rows")
    err_count = df["error"].notna().sum() if "error" in df.columns else 0
    print(f"Errors:  {err_count}")

    df = assign_sectors(df)
    df = compute_sector_zscores(df, sector_col="super_sector", min_sector_size=5)
    df = compute_quality_score(df)

    df = df.sort_values("composite_z", ascending=True, na_position="last")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = build_snapshot(df)

    latest_path = DATA_DIR / "latest.json"
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n✓ Saved: {latest_path}")

    today = datetime.now(KST).strftime("%Y-%m-%d")
    hist_path = HISTORY_DIR / f"{today}.json"
    with open(hist_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2, default=str)

    # 미리보기
    print("\n--- TOP 15 Undervalued (Korea) ---")
    top = df.dropna(subset=["composite_z"]).head(15)
    cols = ["ticker", "short_name", "super_sector", "composite_z", "pe", "ps", "pb", "z_count"]
    print(top[cols].to_string(index=False))
    return df


if __name__ == "__main__":
    main()
