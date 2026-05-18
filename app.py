import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="트렌드 통합 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 공통 스타일 ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: #1e1e2e;
        border-radius: 12px;
        padding: 16px 20px;
        border-left: 4px solid #6c63ff;
    }
    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #a0a0c0;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    div[data-testid="stTabs"] button { font-size: 0.95rem; }
</style>
""", unsafe_allow_html=True)


# ── 사이드바 ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📊 트렌드 대시보드")
    st.caption("Google · 네이버 · YouTube · Meta")
    st.divider()

    st.subheader("🔑 API 키 설정")
    naver_id = st.text_input("네이버 Client ID", value=os.getenv("NAVER_CLIENT_ID", ""), type="password")
    naver_secret = st.text_input("네이버 Client Secret", value=os.getenv("NAVER_CLIENT_SECRET", ""), type="password")
    youtube_key = st.text_input("YouTube API Key", value=os.getenv("YOUTUBE_API_KEY", ""), type="password")
    meta_token = st.text_input("Meta Access Token", value=os.getenv("META_ACCESS_TOKEN", ""), type="password")

    if naver_id:
        os.environ["NAVER_CLIENT_ID"] = naver_id
    if naver_secret:
        os.environ["NAVER_CLIENT_SECRET"] = naver_secret
    if youtube_key:
        os.environ["YOUTUBE_API_KEY"] = youtube_key
    if meta_token:
        os.environ["META_ACCESS_TOKEN"] = meta_token

    st.divider()
    st.subheader("⚙️ 공통 설정")
    keywords_input = st.text_input("비교 키워드 (쉼표 구분)", value="AI, ChatGPT, 클로드")
    keywords = [k.strip() for k in keywords_input.split(",") if k.strip()][:5]

    timeframe_map = {
        "최근 7일": "now 7-d",
        "최근 1개월": "today 1-m",
        "최근 3개월": "today 3-m",
        "최근 12개월": "today 12-m",
    }
    selected_tf_label = st.selectbox("기간", list(timeframe_map.keys()), index=2)
    timeframe = timeframe_map[selected_tf_label]

    refresh = st.button("🔄 데이터 새로고침", use_container_width=True)

st.title("📈 실시간 트렌드 통합 대시보드")
st.caption(f"키워드: {', '.join(keywords)} · 기간: {selected_tf_label}")
st.divider()

# ── 탭 구성 ───────────────────────────────────────────────────────────────────
tab_google, tab_naver, tab_youtube, tab_meta, tab_compare = st.tabs([
    "🔍 Google Trends",
    "🟢 네이버 데이터랩",
    "▶️ YouTube",
    "📘 Meta 광고 라이브러리",
    "📊 통합 비교",
])


# ═══════════════════════════════════════════════════════════════════════════════
# Google Trends 탭
# ═══════════════════════════════════════════════════════════════════════════════
with tab_google:
    st.subheader("Google 검색 트렌드")
    col_btn, _ = st.columns([1, 4])
    load_google = col_btn.button("데이터 불러오기", key="google_load")

    if load_google or refresh:
        from fetchers.google_trends import fetch_interest_over_time, fetch_related_queries, fetch_trending_searches

        with st.spinner("Google Trends에서 데이터를 가져오는 중..."):
            try:
                df_iot = fetch_interest_over_time(keywords, timeframe=timeframe)
                if not df_iot.empty:
                    fig = px.line(
                        df_iot.reset_index().melt(id_vars="date", var_name="키워드", value_name="관심도"),
                        x="date", y="관심도", color="키워드",
                        title="시간별 검색 관심도 (Google, 상대값 0–100)",
                        template="plotly_dark",
                    )
                    fig.update_layout(height=400, legend_title_text="키워드")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("해당 기간에 데이터가 없습니다.")
            except Exception as e:
                st.error(f"Google Trends 오류: {e}")

        st.divider()
        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<p class="section-title">🔥 실시간 급상승 검색어 (한국)</p>', unsafe_allow_html=True)
            try:
                df_trending = fetch_trending_searches("south_korea")
                for i, term in enumerate(df_trending[0].head(10).tolist(), 1):
                    st.write(f"{i}. {term}")
            except Exception as e:
                st.error(f"급상승 검색어 오류: {e}")

        with col2:
            st.markdown('<p class="section-title">🔗 연관 검색어</p>', unsafe_allow_html=True)
            kw_select = st.selectbox("키워드 선택", keywords, key="related_kw")
            try:
                related = fetch_related_queries(kw_select)
                rising_df = related.get("rising")
                if rising_df is not None and not rising_df.empty:
                    st.dataframe(rising_df.head(10), use_container_width=True, hide_index=True)
                else:
                    st.info("급상승 연관 검색어 데이터 없음")
            except Exception as e:
                st.error(f"연관 검색어 오류: {e}")
    else:
        st.info("'데이터 불러오기' 버튼을 눌러 Google Trends 데이터를 조회하세요.")
        st.caption("⚠️ Google Trends는 공식 API가 없어 과도한 요청 시 일시 차단될 수 있습니다.")


# ═══════════════════════════════════════════════════════════════════════════════
# 네이버 데이터랩 탭
# ═══════════════════════════════════════════════════════════════════════════════
with tab_naver:
    st.subheader("네이버 데이터랩 검색어 트렌드")
    col_btn2, _ = st.columns([1, 4])
    load_naver = col_btn2.button("데이터 불러오기", key="naver_load")

    if load_naver or refresh:
        if not os.getenv("NAVER_CLIENT_ID"):
            st.warning("사이드바에서 네이버 Client ID / Secret을 입력해주세요.")
        else:
            from fetchers.naver_datalab import fetch_keyword_trend

            keyword_groups = [{"groupName": kw, "keywords": [kw]} for kw in keywords]

            with st.spinner("네이버 데이터랩에서 데이터를 가져오는 중..."):
                try:
                    df_naver = fetch_keyword_trend(keyword_groups)
                    if not df_naver.empty:
                        fig_naver = px.line(
                            df_naver, x="date", y="ratio", color="group",
                            title="네이버 검색 트렌드 (상대값 0–100)",
                            labels={"date": "날짜", "ratio": "검색량 비율", "group": "키워드"},
                            template="plotly_dark",
                        )
                        fig_naver.update_layout(height=400)
                        st.plotly_chart(fig_naver, use_container_width=True)

                        col_m1, col_m2, col_m3 = st.columns(3)
                        for i, kw in enumerate(df_naver["group"].unique()):
                            kw_df = df_naver[df_naver["group"] == kw]
                            peak = kw_df["ratio"].max()
                            recent = kw_df.sort_values("date").iloc[-1]["ratio"]
                            [col_m1, col_m2, col_m3][i % 3].metric(
                                label=kw,
                                value=f"{recent:.1f}",
                                delta=f"최고 {peak:.1f}",
                            )
                    else:
                        st.info("데이터가 없습니다.")
                except Exception as e:
                    st.error(f"네이버 데이터랩 오류: {e}")
    else:
        st.info("'데이터 불러오기' 버튼을 눌러 네이버 데이터랩 데이터를 조회하세요.")
        st.markdown("""
        **API 발급 방법:**
        1. [네이버 개발자 센터](https://developers.naver.com) 접속
        2. Application 등록 → 데이터랩(검색어 트렌드) 권한 추가
        3. Client ID / Secret 복사 후 사이드바에 입력
        """)


# ═══════════════════════════════════════════════════════════════════════════════
# YouTube 탭
# ═══════════════════════════════════════════════════════════════════════════════
with tab_youtube:
    st.subheader("YouTube 트렌드")

    yt_mode = st.radio("모드", ["인기 급상승 동영상", "키워드 검색"], horizontal=True)
    col_btn3, _ = st.columns([1, 4])
    load_yt = col_btn3.button("데이터 불러오기", key="yt_load")

    if load_yt or refresh:
        if not os.getenv("YOUTUBE_API_KEY"):
            st.warning("사이드바에서 YouTube API Key를 입력해주세요.")
        else:
            from fetchers.youtube_trends import fetch_trending_videos, fetch_keyword_videos

            with st.spinner("YouTube에서 데이터를 가져오는 중..."):
                try:
                    if yt_mode == "인기 급상승 동영상":
                        df_yt = fetch_trending_videos(max_results=20)
                    else:
                        search_kw = st.selectbox("검색 키워드", keywords, key="yt_search_kw")
                        df_yt = fetch_keyword_videos(search_kw, max_results=15)

                    if not df_yt.empty:
                        if "view_count" in df_yt.columns:
                            fig_yt = px.bar(
                                df_yt.head(10),
                                x="view_count", y="title",
                                orientation="h",
                                title="인기 동영상 조회수 Top 10",
                                labels={"view_count": "조회수", "title": ""},
                                template="plotly_dark",
                                color="view_count",
                                color_continuous_scale="Viridis",
                            )
                            fig_yt.update_layout(height=450, showlegend=False, yaxis={"autorange": "reversed"})
                            st.plotly_chart(fig_yt, use_container_width=True)

                        cols = [c for c in ["title", "channel", "published_at", "view_count", "like_count"] if c in df_yt.columns]
                        st.dataframe(
                            df_yt[cols].rename(columns={
                                "title": "제목", "channel": "채널",
                                "published_at": "게시일", "view_count": "조회수", "like_count": "좋아요"
                            }),
                            use_container_width=True, hide_index=True,
                        )
                except Exception as e:
                    st.error(f"YouTube API 오류: {e}")
    else:
        st.info("'데이터 불러오기' 버튼을 눌러 YouTube 트렌드를 조회하세요.")
        st.markdown("""
        **API 발급 방법:**
        1. [Google Cloud Console](https://console.cloud.google.com) 접속
        2. YouTube Data API v3 활성화
        3. 사용자 인증 정보 → API 키 생성 후 사이드바에 입력
        """)


# ═══════════════════════════════════════════════════════════════════════════════
# Meta 광고 라이브러리 탭
# ═══════════════════════════════════════════════════════════════════════════════
with tab_meta:
    st.subheader("Meta 광고 라이브러리")
    meta_search = st.text_input("광고 검색어", value=keywords[0] if keywords else "AI")
    col_btn4, _ = st.columns([1, 4])
    load_meta = col_btn4.button("데이터 불러오기", key="meta_load")

    if load_meta or refresh:
        if not os.getenv("META_ACCESS_TOKEN"):
            st.warning("사이드바에서 Meta Access Token을 입력해주세요.")
        else:
            from fetchers.meta_ad_library import fetch_ads

            with st.spinner("Meta 광고 라이브러리에서 데이터를 가져오는 중..."):
                try:
                    df_meta = fetch_ads(meta_search, limit=20)
                    if not df_meta.empty:
                        col_m1, col_m2 = st.columns(2)
                        col_m1.metric("검색된 광고 수", len(df_meta))
                        col_m2.metric("광고주 수 (유니크)", df_meta["page_name"].nunique())

                        fig_meta = px.bar(
                            df_meta["page_name"].value_counts().head(10).reset_index(),
                            x="count", y="page_name",
                            orientation="h",
                            title="광고주별 광고 수 Top 10",
                            labels={"count": "광고 수", "page_name": "페이지"},
                            template="plotly_dark",
                        )
                        fig_meta.update_layout(height=350, yaxis={"autorange": "reversed"})
                        st.plotly_chart(fig_meta, use_container_width=True)

                        display_cols = [c for c in ["page_name", "title", "body", "created", "impressions_lower", "spend_lower", "currency"] if c in df_meta.columns]
                        st.dataframe(
                            df_meta[display_cols].rename(columns={
                                "page_name": "페이지", "title": "광고 제목", "body": "광고 내용",
                                "created": "생성일", "impressions_lower": "노출수(최소)",
                                "spend_lower": "지출(최소)", "currency": "통화"
                            }),
                            use_container_width=True, hide_index=True,
                        )
                    else:
                        st.info("검색 결과가 없습니다.")
                except Exception as e:
                    st.error(f"Meta Ad Library 오류: {e}")
    else:
        st.info("'데이터 불러오기' 버튼을 눌러 Meta 광고 데이터를 조회하세요.")
        st.markdown("""
        **Access Token 발급 방법:**
        1. [Meta for Developers](https://developers.facebook.com) 접속
        2. 앱 생성 → 광고 라이브러리 API 검토 신청 (또는 단기 User Token 사용)
        3. Graph API Explorer에서 토큰 생성 후 사이드바에 입력
        """)


# ═══════════════════════════════════════════════════════════════════════════════
# 통합 비교 탭
# ═══════════════════════════════════════════════════════════════════════════════
with tab_compare:
    st.subheader("플랫폼 간 트렌드 통합 비교")
    st.caption("Google Trends와 네이버 데이터랩 데이터를 함께 조회해야 비교 차트가 활성화됩니다.")

    col_load1, col_load2, _ = st.columns([1, 1, 3])
    load_compare = col_load1.button("통합 데이터 불러오기", key="compare_load")

    if load_compare:
        from fetchers.google_trends import fetch_interest_over_time
        results = {}
        errors = []

        with st.spinner("Google Trends..."):
            try:
                df_g = fetch_interest_over_time(keywords, timeframe=timeframe)
                if not df_g.empty:
                    df_g_melted = df_g.reset_index().melt(id_vars="date", var_name="keyword", value_name="value")
                    df_g_melted["source"] = "Google"
                    results["google"] = df_g_melted
            except Exception as e:
                errors.append(f"Google: {e}")

        if os.getenv("NAVER_CLIENT_ID"):
            from fetchers.naver_datalab import fetch_keyword_trend
            with st.spinner("네이버 데이터랩..."):
                try:
                    kw_groups = [{"groupName": kw, "keywords": [kw]} for kw in keywords]
                    df_n = fetch_keyword_trend(kw_groups)
                    if not df_n.empty:
                        df_n_renamed = df_n.rename(columns={"group": "keyword", "ratio": "value"})
                        df_n_renamed["source"] = "Naver"
                        results["naver"] = df_n_renamed
                except Exception as e:
                    errors.append(f"Naver: {e}")

        if errors:
            for err in errors:
                st.warning(err)

        if results:
            combined = pd.concat(list(results.values()), ignore_index=True)
            combined["date"] = pd.to_datetime(combined["date"])

            for kw in keywords:
                kw_df = combined[combined["keyword"] == kw]
                if kw_df.empty:
                    continue
                fig_cmp = go.Figure()
                for source, grp in kw_df.groupby("source"):
                    fig_cmp.add_trace(go.Scatter(
                        x=grp["date"], y=grp["value"],
                        mode="lines", name=source,
                        line={"width": 2},
                    ))
                fig_cmp.update_layout(
                    title=f"'{kw}' — 플랫폼 비교",
                    xaxis_title="날짜", yaxis_title="관심도 (정규화)",
                    template="plotly_dark", height=300,
                    legend_title_text="플랫폼",
                )
                st.plotly_chart(fig_cmp, use_container_width=True)

            st.divider()
            st.markdown("### 데이터 요약")
            summary = combined.groupby(["source", "keyword"])["value"].agg(["mean", "max", "min"]).round(1)
            summary.columns = ["평균", "최고", "최저"]
            st.dataframe(summary, use_container_width=True)
        else:
            st.error("불러온 데이터가 없습니다. 위 탭에서 각 플랫폼 데이터를 먼저 확인하세요.")
    else:
        st.info("'통합 데이터 불러오기'를 눌러 플랫폼 간 트렌드를 비교하세요.")

        st.markdown("""
        ### 활성화된 플랫폼
        | 플랫폼 | 상태 |
        |--------|------|
        | Google Trends | ✅ API 키 불필요 |
        | 네이버 데이터랩 | {} |
        | YouTube | {} |
        | Meta 광고 라이브러리 | {} |
        """.format(
            "✅ 연결됨" if os.getenv("NAVER_CLIENT_ID") else "⚠️ API 키 필요",
            "✅ 연결됨" if os.getenv("YOUTUBE_API_KEY") else "⚠️ API 키 필요",
            "✅ 연결됨" if os.getenv("META_ACCESS_TOKEN") else "⚠️ API 키 필요",
        ))
