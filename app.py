import streamlit as st
import pandas as pd

# --- 페이지 기본 설정 ---
st.set_page_config(
    page_title="BoMi - The BOM Analyst",
    page_icon="🤖",
    layout="centered"
)

# --- 루미나: 앱의 비전과 사용법을 설명합니다 ---
st.title("🤖 'BoMi' - BOM 분석 에이전트 MVP v0.1")
st.markdown("""
이 앱은 'AI 모자 디자인 스튜디오'의 첫 번째 두뇌, **BoMi**의 프로토타입입니다.
BOM 데이터를 업로드하고, 원하는 조건을 선택하여 최적의 부품 조합을 찾아보세요.
""")

# --- 델타: 시스템의 핵심 로직을 구현합니다 ---

# 1. 파일 업로더: 사용자가 BOM 데이터를 직접 올리도록 합니다.
uploaded_file = st.file_uploader("BOM 데이터 파일을 업로드하세요 (CSV 또는 Excel)", type=["csv", "xlsx"])

# 파일이 업로드되었을 때만 아래 코드를 실행합니다.
if uploaded_file is not None:
    try:
        # 업로드된 파일 형식에 따라 데이터를 읽어옵니다.
        if uploaded_file.name.endswith('.csv'):
            bom_df = pd.read_csv(uploaded_file)
        else:
            bom_df = pd.read_excel(uploaded_file)

        # 열 이름의 앞뒤 공백을 제거하고 소문자로 변환하여 오류를 방지합니다.
        bom_df.columns = bom_df.columns.str.strip().str.lower()
        
        st.success("BOM 데이터 로딩 완료!")
        st.dataframe(bom_df.head()) # 데이터 미리보기

        # --- BoMi의 '사고' 프로세스: 필터링 인터페이스 ---
        st.markdown("---")
        st.subheader("🔍 부품 검색 조건 설정")

        # 1. 부품 유형(part_type)으로 필터링
        part_types = bom_df['part_type'].unique()
        selected_part_types = st.multiselect(
            "1. 원하는 부품 유형을 선택하세요:",
            options=part_types,
            default=part_types
        )

        # 2. 재질(material)로 필터링
        materials = bom_df['material'].unique()
        selected_materials = st.multiselect(
            "2. 원하는 재질을 선택하세요:",
            options=materials,
            default=materials
        )

        # 3. 최대 단가(unit_cost_usd)로 필터링
        max_cost = float(bom_df['unit_cost_usd'].max())
        cost_limit = st.slider(
            "3. 부품당 최대 단가를 설정하세요 ($):",
            min_value=0.0,
            max_value=max_cost,
            value=max_cost,
            step=0.1
        )

        # --- BoMi의 '행동' 프로세스: 필터링된 결과 표시 ---

        # 선택된 조건에 따라 데이터프레임을 필터링합니다.
        filtered_df = bom_df[
            (bom_df['part_type'].isin(selected_part_types)) &
            (bom_df['material'].isin(selected_materials)) &
            (bom_df['unit_cost_usd'] <= cost_limit)
        ]

        st.markdown("---")
        st.subheader("결과: 조건에 맞는 부품 리스트")

        if filtered_df.empty:
            st.warning("선택하신 조건에 맞는 부품이 없습니다.")
        else:
            # 결과를 깔끔한 테이블 형태로 보여줍니다.
            st.dataframe(filtered_df)

    except Exception as e:
        st.error(f"파일을 처리하는 중 오류가 발생했습니다: {e}")

else:
    st.info("시작하려면 BOM 파일을 업로드해주세요.")

