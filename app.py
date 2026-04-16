import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Coupon Generator", layout="centered")

st.title("🧾 Coupon Generator")
st.caption("롯데온 쿠폰 등록 자동화 MVP")

# --- 입력 영역 ---
st.header("1️⃣ 쿠폰 정보 입력")

brand = st.text_input("브랜드명")
event_name = st.text_input("행사명")
discount_rate = st.number_input("할인율 (%)", min_value=0, max_value=100, value=10)
start_date = st.date_input("시작일")
end_date = st.date_input("종료일")

# 샘플 상품 리스트 (실제는 DB에서 가져와야 함)
st.header("2️⃣ 상품 리스트 (샘플)")
product_ids = st.text_area(
    "상품 ID 입력 (줄바꿈으로 구분)",
    placeholder="12345\n67890\n11111"
)

# --- 처리 ---
if st.button("🚀 CSV 생성"):
    if not brand or not event_name or not product_ids:
        st.error("필수값을 입력하세요.")
    else:
        pid_list = product_ids.split("\n")

        data = []
        for pid in pid_list:
            data.append({
                "상품ID": pid.strip(),
                "브랜드": brand,
                "행사명": event_name,
                "할인율": discount_rate,
                "시작일": start_date,
                "종료일": end_date
            })

        df = pd.DataFrame(data)

        st.success("CSV 생성 완료")

        st.dataframe(df)

        csv = df.to_csv(index=False).encode('utf-8-sig')

        st.download_button(
            label="📥 CSV 다운로드",
            data=csv,
            file_name=f"coupon_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime='text/csv'
        )
