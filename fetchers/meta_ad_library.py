import os
import requests
import pandas as pd


_API_BASE = "https://graph.facebook.com/v19.0/ads_archive"


def _access_token() -> str:
    token = os.getenv("META_ACCESS_TOKEN", "")
    if not token:
        raise EnvironmentError("META_ACCESS_TOKEN 환경변수를 설정하세요.")
    return token


def fetch_ads(
    search_terms: str,
    country: str = "KR",
    limit: int = 20,
    ad_type: str = "ALL",
) -> pd.DataFrame:
    """
    Meta 광고 라이브러리에서 광고를 검색합니다.
    ad_type: ALL | POLITICAL_AND_ISSUE_ADS
    """
    params = {
        "access_token": _access_token(),
        "search_terms": search_terms,
        "ad_reached_countries": country,
        "ad_type": ad_type,
        "limit": limit,
        "fields": (
            "id,ad_creation_time,ad_creative_bodies,ad_creative_link_titles,"
            "ad_delivery_start_time,ad_delivery_stop_time,"
            "page_name,impressions,spend,currency"
        ),
    }
    resp = requests.get(_API_BASE, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    rows = []
    for ad in data.get("data", []):
        bodies = ad.get("ad_creative_bodies") or []
        titles = ad.get("ad_creative_link_titles") or []
        impressions = ad.get("impressions") or {}
        spend = ad.get("spend") or {}
        rows.append({
            "id": ad.get("id"),
            "page_name": ad.get("page_name"),
            "created": ad.get("ad_creation_time", "")[:10],
            "start": ad.get("ad_delivery_start_time", "")[:10],
            "stop": ad.get("ad_delivery_stop_time", "")[:10],
            "body": bodies[0] if bodies else "",
            "title": titles[0] if titles else "",
            "impressions_lower": impressions.get("lower_bound"),
            "impressions_upper": impressions.get("upper_bound"),
            "spend_lower": spend.get("lower_bound"),
            "spend_upper": spend.get("upper_bound"),
            "currency": ad.get("currency", ""),
        })

    return pd.DataFrame(rows)
