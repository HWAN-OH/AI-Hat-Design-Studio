import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import json
import httpx  # For making asynchronous API calls
import asyncio
import yaml

# --- 페이지 기본 설정 ---
st.set_page_config(
    page_title="AI Hat Design Studio",
    page_icon="👒",
    layout="wide"
)

# --- 루미나: 앱의 비전과 사용법을 설명합니다 ---
st.title("👒 AI 모자 디자인 스튜디오 v1.2 (Live & Secure)")
st.markdown("""
**진짜 Gemini AI 엔진이 안전하게 내장되었습니다!**
이제 'Forma'는 당신의 자유로운 말을 실시간으로 이해하고, 그에 맞춰 3D 모델을 수정합니다.
BOM 데이터를 올리고, 초기 모델을 조립한 뒤, 채팅창에 자유롭게 명령을 내려보세요.
""")

# --- 델타: 시스템의 핵심 로직을 구현합니다 ---

# 세션 상태 초기화
if 'hat_config' not in st.session_state:
    st.session_state.hat_config = {
        "parts": [], "logo_scale": 1.0, "brim_color": "#808080"
    }

# --- FIX: API 키를 가장 안전한 방식으로 불러옵니다 ---
# Streamlit Cloud의 'Secrets'에서 API 키를 직접 불러옵니다.
# 이제 더 이상 사용자에게 키를 묻거나, 코드에 키를 노출할 필요가 없습니다.
api_key = st.secrets.get("GOOGLE_AI_API_KEY")

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


# --- LLM 연동을 위한 비동기 함수 ---
async def parse_command_with_llm(command, key, persona, available_parts):
    if not key:
        st.error("Google AI API Key가 Streamlit Secrets에 등록되지 않았습니다. 앱 관리자에게 문의하세요.")
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
    
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"
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

# 1. BoMi: BOM 분석 파트
st.header("Step 1: 'BoMi' - 부품 선택")
uploaded_file = st.file_uploader("BOM 데이터 파일을 업로드하세요 (CSV)", type=["csv"])

if uploaded_file is not None:
    try:
        # Use the uploaded file instead of the cached one if provided
        bom_df = pd.read_csv(uploaded_file)
        bom_df.columns = bom_df.columns.str.strip().str.lower()
        
        st.subheader("선택된 부품 리스트")
        st.dataframe(bom_df)

        if st.button("초기 모델 조립하기", key="initial_assembly"):
            with st.spinner("'Forma'가 초기 모델을 조립합니다..."):
                parts_to_load = []
                for index, row in bom_df.iterrows():
                    parts_to_load.append({"type": row['part_type'], "model_file": row['model_file']})
                st.session_state.hat_config['parts'] = parts_to_load
                st.success("초기 모델이 준비되었습니다. 아래 채팅창에 자유롭게 명령을 내려보세요.")
    except Exception as e:
        st.error(f"파일 처리 중 오류: {e}")

# 2. Forma: 3D 조립 및 대화형 수정 파트
if st.session_state.hat_config['parts']:
    st.markdown("---")
    st.header("Step 2: 'Forma' - 대화형 디자인")
    command = st.text_input("Forma에게 자유롭게 명령을 내리세요 (예: 'make it a cowboy hat')")

    if command:
        if not api_key:
            st.warning("Google AI API 키가 설정되지 않아, LLM 연동이 불가능합니다.")
        else:
            available_parts_list = bom_df.to_dict('records') if bom_df is not None else []
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
                
                # Re-render the component by rerunning the script
                st.experimental_rerun()

    # 3D 뷰어 렌더링
    with st.container():
        github_user = "HWAN-OH"
        github_repo = "AI-Hat-Design-Studio"
        base_url = f"https://raw.githubusercontent.com/{github_user}/{github_repo}/main/models/"
        models_to_load = []
        for part in st.session_state.hat_config['parts']:
             models_to_load.append({"type": part['type'], "url": base_url + part['model_file']})
        config_json = json.dumps(st.session_state.hat_config)
        html_code = f"""
            <!DOCTYPE html><html><head><style>body{{margin:0;}}canvas{{display:block;}}</style></head>
            <body>
                <script type="importmap">{{"imports":{{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}}}</script>
                <script type="module">
                    import * as THREE from 'three';
                    import {{GLTFLoader}} from 'three/addons/loaders/GLTFLoader.js';
                    import {{OrbitControls}} from 'three/addons/controls/OrbitControls.js';
                    const scene=new THREE.Scene();scene.background=new THREE.Color(0xf0f2f5);
                    const camera=new THREE.PerspectiveCamera(75,window.innerWidth/window.innerHeight,0.1,1000);camera.position.set(0,0.1,0.5);
                    const renderer=new THREE.WebGLRenderer({{antialias:true}});renderer.setSize(window.innerWidth,window.innerHeight);document.body.appendChild(renderer.domElement);
                    const ambientLight=new THREE.AmbientLight(0xffffff,1.5);scene.add(ambientLight);
                    const directionalLight=new THREE.DirectionalLight(0xffffff,2);directionalLight.position.set(1,1,1);scene.add(directionalLight);
                    const controls=new OrbitControls(camera,renderer.domElement);
                    const hatConfig={config_json};const models={json.dumps(models_to_load)};
                    const loader=new GLTFLoader();const hatParts=new THREE.Group();scene.add(hatParts);
                    models.forEach(modelData=>{{loader.load(modelData.url,(gltf)=>{{const model=gltf.scene;
                    if(modelData.type.toLowerCase()==='logo'){{model.scale.setScalar(hatConfig.logo_scale||1.0);}}
                    if(modelData.type.toLowerCase()==='brim'){{model.traverse((child)=>{{if(child.isMesh){{child.material=child.material.clone();child.material.color.set(hatConfig.brim_color||"#808080");}}}});}}
                    hatParts.add(model);}});}});
                    function animate(){{requestAnimationFrame(animate);controls.update();renderer.render(scene,camera);}}
                    animate();
                </script>
            </body></html>
        """
        components.html(html_code, height=600, scrolling=False)

