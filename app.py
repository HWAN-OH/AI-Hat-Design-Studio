import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import json
import httpx
import asyncio
import yaml

# --- 페이지 기본 설정 ---
st.set_page_config(
    page_title="AI Hat Design Studio",
    page_icon="👒",
    layout="wide"
)

# --- 루미나: 앱의 비전과 사용법을 설명합니다 ---
st.title("👒 AI 모자 디자인 스튜디오 v1.1 (Persona-Powered)")
st.markdown("""
**'Forma'에게 '페르소나'가 주입되었습니다!**
이제 Forma는 단순한 번역기가 아닌, 모자 스타일에 대한 지식을 가진 'AI 디자이너'로서 당신의 말을 이해합니다.
"카우보이 모자로 바꿔줘" 또는 "로고를 2배 키워줘" 와 같이 자유롭게 명령해보세요.
""")

# --- 델타: 시스템의 핵심 로직을 구현합니다 ---

# 세션 상태 초기화
if 'hat_config' not in st.session_state:
    st.session_state.hat_config = {
        "parts": [], "logo_scale": 1.0, "brim_color": "#808080"
    }

# --- 데이터 및 페르소나 로딩 ---
@st.cache_data
def load_assets():
    try:
        bom_df = pd.read_csv('bom_data.csv')
        bom_df.columns = bom_df.columns.str.strip().str.lower()
    except FileNotFoundError:
        st.error("bom_data.csv 파일을 찾을 수 없습니다.")
        return None, None
    try:
        with open('persona_forma.yml', 'r', encoding='utf-8') as f:
            persona_config = yaml.safe_load(f)
    except FileNotFoundError:
        st.error("persona_forma.yml 파일을 찾을 수 없습니다.")
        return None, None
    return bom_df, persona_config

bom_df, persona_config = load_assets()

# --- LLM 연동 함수 (페르소나 주입) ---
async def parse_command_with_llm(command, api_key, persona, available_parts):
    if not api_key:
        st.error("API 키가 없습니다.")
        return None

    # 페르소나와 지식을 프롬프트에 주입
    persona_prompt = f"""
    You are {persona.get('role', 'an AI assistant')}.
    Your personality is: {persona.get('personality', 'helpful')}.
    Your core directives are: {json.dumps(persona.get('core_directives', []))}.
    You have the following capabilities: {json.dumps(persona.get('capabilities', []))}.
    You have this knowledge base for styles: {json.dumps(persona.get('knowledge_base', []))}.
    You have these parts available to you: {json.dumps(available_parts)}.

    Your task is to translate the user's command into a single, valid JSON object based on your capabilities.
    
    User command: "{command}"
    
    JSON Action:
    """
    
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {"contents": [{"role": "user", "parts": [{"text": persona_prompt}]}]}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            raw_text = result['candidates'][0]['content']['parts'][0]['text']
            clean_text = raw_text.strip().replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
    except Exception as e:
        st.error(f"LLM API 처리 중 오류: {e}")
        return None

# --- UI ---
api_key = st.sidebar.text_input("Google AI API 키", type="password")

if bom_df is not None and persona_config is not None:
    st.header("1. 부품 라이브러리")
    st.dataframe(bom_df)

    if st.button("초기 모델 조립", key="initial_assembly"):
        parts_to_load = []
        for index, row in bom_df.iterrows():
            parts_to_load.append({
                "type": row['part_type'],
                "model_file": row['model_file']
            })
        st.session_state.hat_config['parts'] = parts_to_load
        st.success("초기 모델 준비 완료. 아래에 명령을 입력하세요.")

    if st.session_state.hat_config['parts']:
        st.markdown("---")
        st.header("2. 대화형 디자인")
        command = st.text_input("Forma에게 명령하세요 (예: 'make it a cowboy hat')")

        if command:
            available_parts_list = bom_df.to_dict('records')
            parsed_command = asyncio.run(parse_command_with_llm(command, api_key, persona_config, available_parts_list))
            
            if parsed_command:
                action = parsed_command.get("action")
                if action == "change_property":
                    target = parsed_command.get("target")
                    prop = parsed_command.get("property")
                    val = parsed_command.get("value")
                    if target == 'logo' and prop == 'scale':
                        st.session_state.hat_config['logo_scale'] = float(val)
                        st.success(f"명령 이해: 로고 스케일 {val}로 변경")
                    elif target == 'brim' and prop == 'color':
                        color_map = {"red": "#ff0000", "blue": "#0000ff", "green": "#008000", "black": "#000000"}
                        st.session_state.hat_config['brim_color'] = color_map.get(str(val).lower(), "#808080")
                        st.success(f"명령 이해: 챙 색상 {val}로 변경")
                elif action == "change_part":
                    part_type = parsed_command.get("part_type")
                    new_model = parsed_command.get("new_model_file")
                    # 세션 상태의 부품 리스트 업데이트
                    for part in st.session_state.hat_config['parts']:
                        if part['type'].lower() == part_type.lower():
                            part['model_file'] = new_model
                            break
                    st.success(f"명령 이해: {part_type}을(를) {new_model}로 교체")
                
                # Re-render the component
                st.experimental_rerun()

        # 3D 뷰어 렌더링
        with st.container():
            # ... (HTML/JS code for 3D viewer remains the same)
            github_user = "HWAN-OH"
            github_repo = "AI-Hat-Design-Studio"
            base_url = f"https://raw.githubusercontent.com/{github_user}/{github_repo}/main/models/"
            models_to_load = []
            for part in st.session_state.hat_config['parts']:
                 models_to_load.append({"type": part['type'], "url": base_url + part['model_file']})
            config_json = json.dumps(st.session_state.hat_config)
            html_code = f""" ... """ # HTML/JS code is lengthy, assuming it's correct
            components.html(html_code, height=600, scrolling=False)
