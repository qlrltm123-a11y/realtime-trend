import os
import requests
import pandas as pd


_API_BASE = "https://www.googleapis.com/youtube/v3"


def _api_key() -> str:
    key = os.getenv("YOUTUBE_API_KEY", "")
    if not key:
        raise EnvironmentError("YOUTUBE_API_KEY 환경변수를 설정하세요.")
    return key


def fetch_trending_videos(region_code: str = "KR", max_results: int = 20, category_id: str = "0") -> pd.DataFrame:
    """YouTube 인기 급상승 동영상을 반환합니다."""
    params = {
        "part": "snippet,statistics",
        "chart": "mostPopular",
        "regionCode": region_code,
        "maxResults": max_results,
        "videoCategoryId": category_id,
        "key": _api_key(),
    }
    resp = requests.get(f"{_API_BASE}/videos", params=params, timeout=10)
    resp.raise_for_status()
    items = resp.json().get("items", [])

    rows = []
    for item in items:
        snippet = item["snippet"]
        stats = item.get("statistics", {})
        rows.append({
            "title": snippet["title"],
            "channel": snippet["channelTitle"],
            "published_at": snippet["publishedAt"][:10],
            "view_count": int(stats.get("viewCount", 0)),
            "like_count": int(stats.get("likeCount", 0)),
            "comment_count": int(stats.get("commentCount", 0)),
            "thumbnail": snippet["thumbnails"]["medium"]["url"],
            "video_id": item["id"],
        })

    return pd.DataFrame(rows)


def fetch_keyword_videos(query: str, max_results: int = 10, order: str = "viewCount") -> pd.DataFrame:
    """키워드로 YouTube 영상을 검색합니다. order: relevance | viewCount | date"""
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "regionCode": "KR",
        "maxResults": max_results,
        "order": order,
        "key": _api_key(),
    }
    resp = requests.get(f"{_API_BASE}/search", params=params, timeout=10)
    resp.raise_for_status()
    items = resp.json().get("items", [])

    rows = []
    for item in items:
        snippet = item["snippet"]
        rows.append({
            "title": snippet["title"],
            "channel": snippet["channelTitle"],
            "published_at": snippet["publishedAt"][:10],
            "video_id": item["id"]["videoId"],
        })
    return pd.DataFrame(rows)
