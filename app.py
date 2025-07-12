import streamlit as st
import pandas as pd
import yaml
import asyncio
from translator import get_design_plan_from_llm
from blender_controller import generate_blender_script

# --- Page Configuration & Title ---
st.set_page_config(page_title="AI Hat Design Studio", page_icon="👒", layout="wide")
st.title("👒 AI 모자 디자인 스튜디오 v2.0 (Translator Engine)")
st.markdown("""
이제 시스템은 **Blender 제어 스크립트**를 자동으로 생성합니다.
자연어로 원하는 모자 스타일을 명령하면, 'Forma'가 디자인 계획을 수립하고,
'번역기'가 실행 가능한 Python 스크립트를 만들어 드립니다.
""")

# --- Load Assets ---
@st.cache_data
def load_assets():
    try:
        bom_df = pd.read_csv('bom_data.csv')
        bom_df.columns = bom_df.columns.str.strip().str.lower()
        with open('persona_forma.yml', 'r', encoding='utf-8') as f:
            persona_config = yaml.safe_load(f)
        return bom_df, persona_config
    except FileNotFoundError as e:
        st.error(f"Required file not found: {e.filename}. Please check your repository.")
        return None, None

bom_df, persona_config = load_assets()
api_key = st.secrets.get("GOOGLE_AI_API_KEY")

# --- Main App Logic ---
if bom_df is not None and persona_config is not None:
    st.header("Step 1: 자연어로 디자인 명령하기")
    command = st.text_input(
        "어떤 모자를 만들어 볼까요?", 
        placeholder="예: a classic navy baseball cap with a metal buckle"
    )

    if command:
        if not api_key:
            st.warning("Google AI API 키가 설정되지 않았습니다.")
        else:
            with st.spinner(f"Forma 엔진이 '{command}' 명령을 해석하여 디자인 계획을 수립하는 중..."):
                available_parts = bom_df.to_dict('records')
                design_plan = asyncio.run(get_design_plan_from_llm(command, api_key, persona_config, available_parts))
            
            if design_plan and "error" not in design_plan:
                st.success("디자인 계획 수립 완료!")
                st.json(design_plan)

                st.markdown("---")
                st.header("Step 2: Blender 제어 스크립트 생성")

                with st.spinner("'번역기'가 Python 스크립트를 생성하는 중..."):
                    blender_script = generate_blender_script(design_plan, bom_df)
                
                st.success("Blender 스크립트 생성 완료!")
                
                st.info("아래 코드를 복사하여 Blender의 'Scripting' 탭에 붙여넣고 실행하세요.")
                st.code(blender_script, language='python')

                st.download_button(
                    label="Download Blender Script (.py)",
                    data=blender_script,
                    file_name="design_script.py",
                    mime="text/x-python"
                )
            else:
                st.error(f"LLM이 디자인 계획을 수립하지 못했습니다: {design_plan.get('error', 'Unknown error')}")

