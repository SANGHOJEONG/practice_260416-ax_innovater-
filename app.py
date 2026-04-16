import streamlit as st
import pandas as pd
import io
from datetime import datetime

# ── 페이지 설정 ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="롯데온 Pro | 쿠폰 대량 업로드 시스템",
    page_icon="🎟️",
    layout="wide",
)

# ── 데이터 로드 (MVP 단계: CSV 활용) ──────────────────────────────────────────
@st.cache_data
def load_data():
    try:
        # 파일명을 'dummy_data.xlsx - Sheet1.csv'로 하거나 업로드된 이름에 맞게 수정 가능
        df = pd.read_csv('dummy_data.xlsx - Sheet1.csv')
        return df
    except FileNotFoundError:
        st.error("데이터 파일(dummy_data.xlsx - Sheet1.csv)을 찾을 수 없습니다.")
        return pd.DataFrame()

df_master = load_data()

# ── 사이드바 필터 ─────────────────────────────────────────────────────────────
st.sidebar.header("🔍 상품 검색 필터")

if not df_master.empty:
    # 1. 점포 선택
    stores = st.sidebar.multiselect("점포(상위거래처) 선택", options=sorted(df_master['상위거래처'].unique()))
    
    # 2. 브랜드 선택 (점포 필터링 반영)
    brand_options = df_master[df_master['상위거래처'].isin(stores)]['브랜드명'].unique() if stores else df_master['브랜드명'].unique()
    brands = st.sidebar.multiselect("브랜드 선택", options=sorted(brand_options))
    
    # 3. 상태 선택 (전시/미전시/전체)
    status_filter = st.sidebar.radio("상품 상태", ("전체", "전시", "미전시"), index=0)

    # 데이터 필터링 로직
    filtered_df = df_master.copy()
    if stores:
        filtered_df = filtered_df[filtered_df['상위거래처'].isin(stores)]
    if brands:
        filtered_df = filtered_df[filtered_df['브랜드명'].isin(brands)]
    if status_filter != "전체":
        filtered_df = filtered_df[filtered_df['상태'] == status_filter]
else:
    filtered_df = pd.DataFrame()

# ── 메인 화면 ─────────────────────────────────────────────────────────────────
st.title("🎟️ 롯데온 Pro 쿠폰 업로드 파일 생성기")
st.markdown("---")

tab1, tab2 = st.tabs(["📝 쿠폰 설정 및 생성", "📊 데이터 미리보기"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📍 기본 설정")
        shop_range = st.selectbox("매장범위", options=["A", "M", "O"], help="A:전채널, M:본매장, O:외부채널")
        
        discount_type = st.radio("할인유형", ["정률(10)", "정액(20)"], horizontal=True)
        type_code = "10" if "정률" in discount_type else "20"
        
        discount_val = st.number_input("할인액/율 입력", min_value=0, step=1)
        
    with col2:
        st.subheader("📅 기간 및 분담율")
        start_date = st.date_input("행사 시작일", datetime.now())
        end_date = st.date_input("행사 종료일", datetime.now())
        
        v_share = st.number_input("거래처 분담율 (%)", min_value=0, max_value=100, value=50)
        p_share = 100 - v_share
        st.info(f"제휴사 분담율: {p_share}% (합계 100% 자동 계산)")

    st.markdown("---")
    
    # 업로드용 데이터 생성 로직
    if st.button("🚀 업로드용 파일 생성", use_container_width=True):
        if filtered_df.empty:
            st.warning("필터링된 상품이 없습니다. 사이드바에서 조건을 선택해주세요.")
        else:
            # 양식에 맞춘 데이터프레임 구성
            upload_df = pd.DataFrame()
            upload_df['상품번호'] = filtered_df['상품번호']
            upload_df['매장범위'] = shop_range
            upload_df['행사시작일'] = start_date.strftime('%Y%m%d') + "0000"
            upload_df['행사종료일'] = end_date.strftime('%Y%m%d') + "2359"
            upload_df['할인유형'] = type_code
            upload_df['할인액'] = discount_val
            upload_df['거래처분담율'] = v_share
            upload_df['제휴사분담율'] = p_share
            upload_df['사용요일'] = "OOOOOOO" # 기본값
            upload_df['시작시간'] = "0000"
            upload_df['종료시간'] = "2359"
            upload_df['요일/시간 할인율'] = "" # 필요시 추가 입력

            # 엑셀 파일로 변환
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                upload_df.to_excel(writer, index=False, sheet_name='Sheet1')
            
            st.success(f"총 {len(upload_df)}건의 상품에 대한 파일이 생성되었습니다!")
            st.download_button(
                label="📥 생성된 엑셀 파일 다운로드",
                data=output.getvalue(),
                file_name=f"롯데온_쿠폰업로드_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

with tab2:
    st.subheader("📋 대상 상품 리스트 (필터 결과)")
    st.write(f"현재 선택된 상품 수: {len(filtered_df)}개")
    st.dataframe(filtered_df, use_container_width=True)
