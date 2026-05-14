"""
KOSPI Valuation Radar - Universe Definition (v2, 분류 오류 수정)

한국 시장 특화 분류:
- 반도체 (메모리/비메모리/장비)
- 2차전지 (셀/소재)
- 자동차 (완성차/부품)
- 바이오 (대형/중소)
- IT/플랫폼/게임/엔터
- 화학/소재/철강
- 금융 (은행/증권/보험)
- 조선/방산
- 통신/미디어
- 유통/소비재/음식료
- 건설/에너지/유틸리티
- 운송/물류

yfinance suffix:
- 코스피: .KS  / 코스닥: .KQ
"""
from __future__ import annotations
from typing import Dict, List

UNIVERSE: Dict[str, List[str]] = {
    # ===== 반도체 =====
    "반도체 - 메모리/Logic": [
        "005930.KS", "000660.KS", "005935.KS", "402340.KS",
        "042700.KS", "108320.KS",
    ],
    "반도체 - 장비/소재": [
        "240810.KS", "058470.KQ", "095340.KQ", "036930.KQ",
        "140860.KQ", "095610.KQ", "067310.KQ", "131970.KQ",
        "475150.KQ", "278280.KQ", "121600.KQ",
    ],
    "반도체 - 디스플레이/PCB": [
        "034220.KS", "009150.KS", "098460.KQ",
    ],

    # ===== 2차전지 =====
    "2차전지 - 셀/완제품": [
        "373220.KS", "006400.KS", "096770.KS",
    ],
    "2차전지 - 소재/장비": [
        "247540.KQ", "086520.KQ", "066970.KQ", "298050.KS", "066980.KQ",
    ],

    # ===== 자동차 =====
    "자동차 - 완성차": [
        "005380.KS", "000270.KS", "005385.KS",
    ],
    "자동차 - 부품/EV": [
        "012330.KS", "204320.KS", "018880.KS", "011210.KS",
        "025540.KS", "161390.KS", "073240.KS",
    ],

    # ===== 바이오/제약 =====
    "바이오 - 대형": [
        "207940.KS", "068270.KS", "326030.KS", "302440.KS",
        "000100.KS", "009420.KS", "008930.KS",
    ],
    "바이오 - 중소": [
        "196170.KQ", "950140.KQ", "145020.KQ", "214450.KQ",
        "298380.KQ", "328130.KQ", "095700.KQ",
    ],

    # ===== IT/플랫폼/게임/엔터 =====
    "IT - 플랫폼/SW": [
        "035420.KS", "035720.KS", "377300.KS", "323410.KS", "108860.KQ",
    ],
    "IT - 게임": [
        "259960.KS", "036570.KS", "251270.KS", "112040.KQ",
        "078340.KQ", "263750.KQ", "194480.KQ",
    ],
    "IT - 엔터/콘텐츠": [
        "352820.KS", "041510.KQ", "035900.KQ", "122870.KS",
        "036420.KQ", "079160.KS",
    ],

    # ===== 화학/소재/철강 =====
    "화학/정유": [
        "051910.KS", "010950.KS", "011170.KS", "006650.KS",
        "298000.KS", "298020.KS", "001740.KS",
    ],
    "철강/소재": [
        "003670.KS", "004020.KS", "010130.KS", "002380.KS", "010060.KS",
    ],

    # ===== 조선/방산 =====
    "조선/해운": [
        "009540.KS", "010140.KS", "042660.KS", "329180.KS",
        "075580.KS", "011200.KS", "180640.KS", "003490.KS",
    ],
    "방산/항공": [
        "012450.KS", "047810.KS", "079550.KS", "272210.KS", "064350.KS",
    ],

    # ===== 금융 =====
    "금융 - 은행/지주": [
        "055550.KS", "105560.KS", "086790.KS", "316140.KS",
        "024110.KS", "138930.KS", "175330.KS",
    ],
    "금융 - 증권/보험": [
        "032830.KS", "088350.KS", "000810.KS", "005830.KS",
        "006800.KS", "016360.KS", "039490.KS", "071050.KS",
    ],

    # ===== 통신 =====
    "통신": [
        "017670.KS", "030200.KS", "032640.KS",
    ],

    # ===== 유통/소비재 =====
    "유통/소비재": [
        "139480.KS", "023530.KS", "069960.KS", "004170.KS",
        "282330.KS", "008770.KS", "215000.KQ", "035250.KS",
    ],
    "음식료/생활": [
        "097950.KS", "001040.KS", "271560.KS", "033780.KS",
        "021240.KS", "090430.KS", "051900.KS", "004990.KS", "280360.KS",
    ],

    # ===== 건설/유틸리티 =====
    "건설": [
        "000720.KS", "047040.KS", "028260.KS", "001230.KS",
        "375500.KS", "006360.KS", "294870.KS",
    ],
    "유틸리티/에너지": [
        "015760.KS", "036460.KS", "267250.KS", "267260.KS", "112610.KS",
    ],

    # ===== 운송/물류/종합상사 =====
    "운송/물류/종합상사": [
        "086280.KS", "001120.KS", "319400.KQ",
    ],
}


SUPER_SECTOR_MAP: Dict[str, str] = {
    "반도체 - 메모리/Logic":         "반도체",
    "반도체 - 장비/소재":            "반도체",
    "반도체 - 디스플레이/PCB":       "반도체",
    "2차전지 - 셀/완제품":           "2차전지",
    "2차전지 - 소재/장비":           "2차전지",
    "자동차 - 완성차":               "자동차",
    "자동차 - 부품/EV":              "자동차",
    "바이오 - 대형":                 "바이오/제약",
    "바이오 - 중소":                 "바이오/제약",
    "IT - 플랫폼/SW":               "IT/플랫폼/게임/엔터",
    "IT - 게임":                    "IT/플랫폼/게임/엔터",
    "IT - 엔터/콘텐츠":             "IT/플랫폼/게임/엔터",
    "화학/정유":                    "화학/소재",
    "철강/소재":                    "화학/소재",
    "조선/해운":                    "조선/방산",
    "방산/항공":                    "조선/방산",
    "금융 - 은행/지주":             "금융",
    "금융 - 증권/보험":             "금융",
    "통신":                         "통신/미디어",
    "유통/소비재":                  "유통/소비재",
    "음식료/생활":                  "유통/소비재",
    "건설":                         "건설/에너지",
    "유틸리티/에너지":              "건설/에너지",
    "운송/물류/종합상사":           "운송/물류",
}


def get_super_sector(sector: str) -> str:
    return SUPER_SECTOR_MAP.get(sector, sector)


def get_all_tickers() -> List[str]:
    seen = set()
    result = []
    for tickers in UNIVERSE.values():
        for t in tickers:
            if t not in seen:
                seen.add(t)
                result.append(t)
    return result


def get_ticker_to_sector() -> Dict[str, str]:
    mapping = {}
    for sector, tickers in UNIVERSE.items():
        for t in tickers:
            if t not in mapping:
                mapping[t] = sector
    return mapping


def get_ticker_to_super_sector() -> Dict[str, str]:
    base = get_ticker_to_sector()
    return {t: get_super_sector(s) for t, s in base.items()}


def get_sector_tickers(sector: str) -> List[str]:
    return UNIVERSE.get(sector, [])


if __name__ == "__main__":
    all_t = get_all_tickers()
    print(f"Total unique tickers: {len(all_t)}")
    print(f"Sub-sectors: {len(UNIVERSE)}")
    print(f"Super-sectors: {len(set(SUPER_SECTOR_MAP.values()))}")
    print()
    from collections import Counter
    super_counts = Counter(get_ticker_to_super_sector().values())
    for sec, n in sorted(super_counts.items(), key=lambda x: -x[1]):
        print(f"  {sec:25s}: {n:3d}")
