import time
import pandas as pd
from pytrends.request import TrendReq
from pytrends.exceptions import TooManyRequestsError


def fetch_interest_over_time(keywords: list[str], timeframe: str = "today 3-m", geo: str = "KR") -> pd.DataFrame:
    """키워드 목록의 시간별 관심도를 반환합니다."""
    pytrends = TrendReq(hl="ko-KR", tz=540)
    # pytrends는 한 번에 최대 5개 키워드
    keywords = keywords[:5]
    try:
        pytrends.build_payload(keywords, timeframe=timeframe, geo=geo)
        df = pytrends.interest_over_time()
        if "isPartial" in df.columns:
            df = df.drop(columns=["isPartial"])
        return df
    except TooManyRequestsError:
        time.sleep(60)
        raise RuntimeError("Google Trends 요청 한도 초과 — 잠시 후 다시 시도하세요.")


def fetch_related_queries(keyword: str, geo: str = "KR") -> dict:
    """특정 키워드의 연관 검색어(급상승 / 상위)를 반환합니다."""
    pytrends = TrendReq(hl="ko-KR", tz=540)
    pytrends.build_payload([keyword], timeframe="today 1-m", geo=geo)
    related = pytrends.related_queries()
    result = related.get(keyword, {})
    return {
        "rising": result.get("rising"),
        "top": result.get("top"),
    }


def fetch_trending_searches(geo: str = "south_korea") -> pd.DataFrame:
    """실시간 급상승 검색어를 반환합니다."""
    pytrends = TrendReq(hl="ko-KR", tz=540)
    return pytrends.trending_searches(pn=geo)
