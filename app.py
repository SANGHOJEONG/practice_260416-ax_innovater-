import streamlit as st
import pandas as pd
import io
from datetime import datetime, date, time

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="롯데온 Pro | 쿠폰 대량 업로드",
    page_icon="🎟️",
    layout="wide",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #f8f4ff; }
    .metric-card {
        background: #ffffff;
        border: 1px solid #e0d7f7;
        border-radius: 10px;
        padding: 16px 20px;
        text-align: center;
    }
    .metric-card .label { font-size: 0.82rem; color: #666; margin-bottom: 4px; }
    .metric-card .value { font-size: 1.6rem; font-weight: 700; color: #5b21b6; }
    .section-title {
        font-size: 1.05rem; font-weight: 700;
        border-left: 4px solid #7c3aed;
        padding-left: 10px; margin: 24px 0 12px;
    }
    .badge-ok   { background:#dcfce7; color:#15803d; border-radius:6px; padding:2px 8px; font-size:.8rem; }
    .badge-warn { background:#fef9c3; color:#a16207; border-radius:6px; padding:2px 8px; font-size:.8rem; }
    .badge-err  { background:#fee2e2; color:#b91c1c; border-radius:6px; padding:2px 8px; font-size:.8rem; }
</style>
""", unsafe_allow_html=True)

# ── Demo seed data ────────────────────────────────────────────────────────────
@st.cache_data
def load_demo_data() -> pd.DataFrame:
    import random
    stores = {
        "롯데백화점 본점": ["나이키", "아디다스", "폴로"],
        "롯데백화점 잠실점": ["MLB", "타미힐피거", "나이키"],
        "롯데아울렛 광명점": ["아디다스", "MLB", "리복"],
    }
    rows = []
    for store, brands in stores.items():
        for brand in brands:
            for i in range(1, 16):
                rows.append({
                    "상위거래처": store,
                    "브랜드명": brand,
                    "상품번호": f"{brand[:2].upper()}{store[:2]}{i:04d}",
                    "상품명": f"{brand} 상품 {i:02d}",
                    "판매가": random.randint(3, 30) * 10000,
                    "전시여부": random.choice(["전시", "전시", "미전시"]),
                })
    return pd.DataFrame(rows)

ALL_DATA = load_demo_data()

# ── Session state init ────────────────────────────────────────────────────────
if "templates" not in st.session_state:
    st.session_state["templates"] = {}
if "history" not in st.session_state:
    st.session_state["history"] = []

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR – ① 데이터 필터링
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🎟️ 쿠폰 대량 업로드")
    st.caption("롯데온 Pro · AMD 전용")
    st.divider()

    st.markdown("### ① 데이터 필터링")

    all_stores = sorted(ALL_DATA["상위거래처"].unique())
    selected_store = st.selectbox("점포 (상위거래처)", ["전체"] + all_stores)

    if selected_store == "전체":
        brand_pool = sorted(ALL_DATA["브랜드명"].unique())
    else:
        brand_pool = sorted(ALL_DATA[ALL_DATA["상위거래처"] == selected_store]["브랜드명"].unique())
    selected_brand = st.selectbox("브랜드명", brand_pool)

    status_opt = st.radio(
        "상품 상태",
        ["전시 상품만", "미전시 상품만", "전체 (전시+미전시)"],
        index=0,
    )
    status_map = {
        "전시 상품만": "전시",
        "미전시 상품만": "미전시",
        "전체 (전시+미전시)": None,
    }
    status_filter = status_map[status_opt]

    filtered = ALL_DATA.copy()
    if selected_store != "전체":
        filtered = filtered[filtered["상위거래처"] == selected_store]
    filtered = filtered[filtered["브랜드명"] == selected_brand]
    if status_filter:
        filtered = filtered[filtered["전시여부"] == status_filter]

    st.markdown(
        f"<span class='badge-ok'>✅ {len(filtered)}개 상품 추출됨</span>"
        if len(filtered) > 0 else
        "<span class='badge-err'>❌ 조건에 맞는 상품 없음</span>",
        unsafe_allow_html=True,
    )
    st.divider()

    st.markdown("### 📂 템플릿")
    tmpl_names = list(st.session_state["templates"].keys())
    if tmpl_names:
        tmpl_sel = st.selectbox("저장된 템플릿", ["선택 안 함"] + tmpl_names)
        load_tmpl = tmpl_sel != "선택 안 함"
    else:
        tmpl_sel = None
        load_tmpl = False
        st.caption("저장된 템플릿 없음")

# ══════════════════════════════════════════════════════════════════════════════
# MAIN – Header
# ══════════════════════════════════════════════════════════════════════════════
st.title("🎟️ 쿠폰 대량 업로드 지원 App")
st.caption("롯데온 Pro 업로드 양식에 맞는 쿠폰 파일을 자동 생성합니다.")

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f"""<div class="metric-card">
        <div class="label">조회 점포</div>
        <div class="value" style="font-size:1.1rem">{selected_store}</div>
    </div>""", unsafe_allow_html=True)
with m2:
    st.markdown(f"""<div class="metric-card">
        <div class="label">선택 브랜드</div>
        <div class="value" style="font-size:1.1rem">{selected_brand}</div>
    </div>""", unsafe_allow_html=True)
with m3:
    st.markdown(f"""<div class="metric-card">
        <div class="label">추출 상품 수</div>
        <div class="value">{len(filtered)}</div>
    </div>""", unsafe_allow_html=True)
with m4:
    st.markdown(f"""<div class="metric-card">
        <div class="label">상품 상태</div>
        <div class="value" style="font-size:1.1rem">{status_opt.split()[0]}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("")

# ── 템플릿 값 로드 헬퍼 ────────────────────────────────────────────────────
def tmpl_val(key, default):
    if load_tmpl and tmpl_sel and tmpl_sel in st.session_state["templates"]:
        return st.session_state["templates"][tmpl_sel].get(key, default)
    return default

tab_input, tab_preview, tab_history = st.tabs(
    ["📝 입력 설정", "🔍 데이터 미리보기", "📋 작업 이력"]
)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 – ② 사용자 입력 인터페이스
# ══════════════════════════════════════════════════════════════════════════════
with tab_input:

    col_left, col_right = st.columns(2, gap="large")

    with col_left:
        st.markdown("<div class='section-title'>📍 매장 범위 설정</div>", unsafe_allow_html=True)
        store_range = st.radio(
            "매장범위",
            ["A (전채널)", "M (본매장)", "O (외부매장)"],
            index=["A (전채널)", "M (본매장)", "O (외부매장)"].index(
                tmpl_val("store_range", "A (전채널)")
            ),
            horizontal=True,
        )
        store_code = store_range.split()[0]

        st.markdown("<div class='section-title'>📅 행사 기간 설정</div>", unsafe_allow_html=True)
        date_col1, date_col2 = st.columns(2)
        with date_col1:
            start_date = st.date_input("시작일", value=tmpl_val("start_date", date.today()))
            start_time = st.time_input("시작 시간", value=tmpl_val("start_time", time(0, 0)), step=3600)
        with date_col2:
            end_date = st.date_input("종료일", value=tmpl_val("end_date", date.today()), min_value=start_date)
            end_time = st.time_input("종료 시간", value=tmpl_val("end_time", time(23, 59)), step=3600)

        start_dt = datetime.combine(start_date, start_time).strftime("%Y%m%d%H%M")
        end_dt   = datetime.combine(end_date,   end_time  ).strftime("%Y%m%d%H%M")
        st.caption(f"시작: `{start_dt}` → 종료: `{end_dt}`")

        if datetime.combine(end_date, end_time) <= datetime.combine(start_date, start_time):
            st.error("❌ 종료 일시가 시작 일시보다 앞설 수 없습니다.")
            date_ok = False
        else:
            date_ok = True

    with col_right:
        st.markdown("<div class='section-title'>💸 할인 정책 설정</div>", unsafe_allow_html=True)
        discount_type_label = st.radio(
            "할인 유형",
            ["정률 (10)", "정액 (20)"],
            index=["정률 (10)", "정액 (20)"].index(tmpl_val("discount_type_label", "정률 (10)")),
            horizontal=True,
        )
        discount_code = "10" if "정률" in discount_type_label else "20"
        discount_unit = "%" if discount_code == "10" else "원"

        discount_value = st.number_input(
            f"할인 {'율' if discount_code=='10' else '액'} ({discount_unit})",
            min_value=1,
            max_value=100 if discount_code == "10" else 1_000_000,
            value=int(tmpl_val("discount_value", 10)),
            step=1 if discount_code == "10" else 1000,
        )
        if discount_code == "10" and discount_value > 80:
            st.warning("⚠️ 할인율이 80%를 초과합니다. 확인해주세요.")

        st.markdown("<div class='section-title'>🤝 비용 분담 설정</div>", unsafe_allow_html=True)
        vendor_share = st.number_input(
            "거래처 분담율 (%)", min_value=0, max_value=100,
            value=int(tmpl_val("vendor_share", 50)), step=5,
        )
        partner_share = st.number_input(
            "제휴사 분담율 (%)", min_value=0, max_value=100,
            value=int(tmpl_val("partner_share", 50)), step=5,
        )
        total_share = vendor_share + partner_share
        if total_share == 100:
            st.markdown("<span class='badge-ok'>✅ 분담율 합계 100% 충족</span>", unsafe_allow_html=True)
            share_ok = True
        else:
            st.markdown(
                f"<span class='badge-err'>❌ 분담율 합계 {total_share}% — 100%이어야 합니다</span>",
                unsafe_allow_html=True,
            )
            share_ok = False

    # ── 행사명 + 템플릿 저장 ──────────────────────────────────────────────
    st.markdown("<div class='section-title'>📌 행사 정보</div>", unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    with c1:
        campaign_name = st.text_input(
            "행사명 *",
            value=tmpl_val("campaign_name", ""),
            placeholder="예) 나이키 여름 시즌오프 2025",
        )
    with c2:
        tmpl_save_name = st.text_input("템플릿 저장명", placeholder="예) 기본 10% 정률")

    if st.button("💾 현재 설정을 템플릿으로 저장", use_container_width=True):
        if tmpl_save_name.strip():
            st.session_state["templates"][tmpl_save_name.strip()] = {
                "store_range": store_range,
                "start_date": start_date,
                "start_time": start_time,
                "end_date": end_date,
                "end_time": end_time,
                "discount_type_label": discount_type_label,
                "discount_value": discount_value,
                "vendor_share": vendor_share,
                "partner_share": partner_share,
                "campaign_name": campaign_name,
            }
            st.success(f"템플릿 '{tmpl_save_name}' 저장 완료!")
        else:
            st.warning("템플릿 저장명을 입력하세요.")

    st.divider()

    # ── ③ 검증 요약 ──────────────────────────────────────────────────────
    all_ok = (len(filtered) > 0 and share_ok and date_ok and bool(campaign_name.strip()))

    status_items = [
        ("추출 상품 수",  len(filtered) > 0,           f"{len(filtered)}개"),
        ("분담율 합계",   share_ok,                    f"{total_share}%"),
        ("행사 기간",     date_ok,                     f"{start_dt} ~ {end_dt}"),
        ("행사명 입력",   bool(campaign_name.strip()),  campaign_name or "(미입력)"),
    ]
    check_cols = st.columns(4)
    for col, (label, ok, val) in zip(check_cols, status_items):
        badge = "badge-ok" if ok else "badge-err"
        icon  = "✅" if ok else "❌"
        col.markdown(
            f"<div class='metric-card'>"
            f"<div class='label'>{label}</div>"
            f"<div style='margin-top:4px'><span class='{badge}'>{icon} {val}</span></div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("")

    # ── ④ 파일 생성 ──────────────────────────────────────────────────────
    if all_ok:
        out = filtered[["상품번호", "상품명", "판매가", "상위거래처", "브랜드명"]].copy()
        out["행사명"]       = campaign_name
        out["매장범위"]     = store_code
        out["할인유형코드"] = discount_code
        out["할인유형명"]   = "정률" if discount_code == "10" else "정액"
        out["할인값"]       = discount_value
        out["쿠폰시작일시"] = start_dt
        out["쿠폰종료일시"] = end_dt
        out["거래처분담율"] = vendor_share
        out["제휴사분담율"] = partner_share

        col_order = [
            "상품번호", "상품명", "판매가", "행사명",
            "매장범위", "할인유형코드", "할인유형명", "할인값",
            "쿠폰시작일시", "쿠폰종료일시",
            "거래처분담율", "제휴사분담율",
            "상위거래처", "브랜드명",
        ]
        out = out[col_order]
        st.session_state["preview_df"] = out

        csv_bytes = out.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        xlsx_buf = io.BytesIO()
        with pd.ExcelWriter(xlsx_buf, engine="openpyxl") as writer:
            out.to_excel(writer, index=False, sheet_name="쿠폰업로드")
        xlsx_bytes = xlsx_buf.getvalue()

        fname_base = f"coupon_{selected_brand}_{start_date.strftime('%Y%m%d')}"

        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button(
                "⬇️ CSV 다운로드",
                data=csv_bytes,
                file_name=f"{fname_base}.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True,
            )
        with dl2:
            st.download_button(
                "⬇️ Excel (.xlsx) 다운로드",
                data=xlsx_bytes,
                file_name=f"{fname_base}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
            )

        if st.button("📋 작업 이력 저장", use_container_width=True):
            st.session_state["history"].append({
                "저장 시각":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "행사명":     campaign_name,
                "브랜드":     selected_brand,
                "점포":       selected_store,
                "상품 수":    len(out),
                "할인":       f"{'정률' if discount_code=='10' else '정액'} {discount_value}{discount_unit}",
                "기간":       f"{start_dt} ~ {end_dt}",
                "매장범위":   store_code,
                "거래처분담": f"{vendor_share}%",
                "제휴사분담": f"{partner_share}%",
            })
            st.success("이력이 저장되었습니다.")
    else:
        st.button("⬇️ 파일 생성", disabled=True, use_container_width=True, type="primary")
        st.caption("위 4가지 항목이 모두 충족되면 파일 생성 버튼이 활성화됩니다.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 – 데이터 미리보기
# ══════════════════════════════════════════════════════════════════════════════
with tab_preview:
    st.markdown("### 📦 추출 상품 목록")
    st.dataframe(filtered.reset_index(drop=True), use_container_width=True, height=280)

    if "preview_df" in st.session_state:
        st.markdown("### 📄 업로드 양식 미리보기 (최종 생성 파일)")
        st.dataframe(
            st.session_state["preview_df"].reset_index(drop=True),
            use_container_width=True,
            height=320,
        )
    else:
        st.info("입력 설정 탭에서 모든 조건을 충족하면 최종 파일 미리보기가 여기에 표시됩니다.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 – 작업 이력
# ══════════════════════════════════════════════════════════════════════════════
with tab_history:
    st.markdown("### 📋 바이어 작업 이력")
    if st.session_state["history"]:
        hist_df = pd.DataFrame(st.session_state["history"])
        st.dataframe(hist_df, use_container_width=True)
        if st.button("🗑️ 이력 초기화"):
            st.session_state["history"] = []
            st.rerun()
    else:
        st.info("저장된 작업 이력이 없습니다. 파일 생성 후 '작업 이력 저장' 버튼을 눌러주세요.")
