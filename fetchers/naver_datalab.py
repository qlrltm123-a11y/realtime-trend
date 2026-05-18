import os
import json
import requests
import pandas as pd
from datetime import datetime, timedelta


_API_URL = "https://openapi.naver.com/v1/datalab/search"


def _headers() -> dict:
    client_id = os.getenv("NAVER_CLIENT_ID", "")
    client_secret = os.getenv("NAVER_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        raise EnvironmentError("NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 환경변수를 설정하세요.")
    return {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
        "Content-Type": "application/json",
    }


def fetch_keyword_trend(
    keyword_groups: list[dict],
    start_date: str | None = None,
    end_date: str | None = None,
    time_unit: str = "date",
    device: str = "",
    ages: list[str] | None = None,
    gender: str = "",
) -> pd.DataFrame:
    """
    네이버 데이터랩 검색어 트렌드를 조회합니다.

    keyword_groups 예시:
        [{"groupName": "AI", "keywords": ["ChatGPT", "클로드"]}, ...]
    time_unit: date | week | month
    """
    if end_date is None:
        end_date = datetime.today().strftime("%Y-%m-%d")
    if start_date is None:
        start_date = (datetime.today() - timedelta(days=90)).strftime("%Y-%m-%d")

    body = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": time_unit,
        "keywordGroups": keyword_groups,
        "device": device,
        "ages": ages or [],
        "gender": gender,
    }

    resp = requests.post(_API_URL, headers=_headers(), data=json.dumps(body), timeout=10)
    resp.raise_for_status()
    data = resp.json()

    rows = []
    for result in data.get("results", []):
        group_name = result["title"]
        for point in result["data"]:
            rows.append({"date": point["period"], "group": group_name, "ratio": point["ratio"]})

    df = pd.DataFrame(rows)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df
