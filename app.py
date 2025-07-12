import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import json
import httpx
import asyncio

# --- 페이지 기본 설정 ---
st.set_page_config(
    page_title="AI Hat Design Studio",
    page_icon="👒",
    layout="wide"
)

# --- 루미나: 앱의 비전과 사용법을 설명합니다 ---
st.title("👒 AI 모자 디자인 스튜디오 v1.0 (Live & Secure)")
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

# --- LLM 연동을 위한 비동기 함수 ---
async def parse_command_with_llm(command, key):
    if not key:
        st.error("Google AI API Key가 Streamlit Secrets에 등록되지 않았습니다. 관리자에게 문의하세요.")
        return None

    st.info(f"Forma가 명령을 해석하는 중입니다: '{command}'")
    
    prompt = f"""
    You are an AI assistant that parses natural language commands for a 3D hat designer.
    Your task is to extract the target part, the property to change, and the new value from the user's command.
    Your response MUST be a valid JSON object with ONLY the keys "target", "property", and "value".

    Examples:
    - User: "make the logo 2 times bigger" -> {{"target": "logo", "property": "scale", "value": 2.0}}
    - User: "change brim color to blue" -> {{"target": "brim", "property": "color", "value": "blue"}}
    Now, parse: "{command}" ->
    """
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"
    payload = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
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
    command = st.text_input("Forma에게 자유롭게 명령을 내리세요 (예: 'make the logo bigger' 또는 'I want a red brim')")

    if command:
        parsed_command = asyncio.run(parse_command_with_llm(command, api_key))
        if parsed_command:
            target = parsed_command.get("target")
            prop = parsed_command.get("property")
            val = parsed_command.get("value")
            if target == 'logo' and prop == 'scale':
                st.session_state.hat_config['logo_scale'] = float(val)
                st.success(f"LLM이 명령을 이해했습니다: 로고 스케일을 {val}로 변경합니다.")
            elif target == 'brim' and prop == 'color':
                color_map = {"red": "#ff0000", "blue": "#0000ff", "green": "#008000", "black": "#000000", "gray": "#808080"}
                st.session_state.hat_config['brim_color'] = color_map.get(str(val).lower(), "#808080")
                st.success(f"LLM이 명령을 이해했습니다: 챙 색상을 {val}로 변경합니다.")
            else:
                st.warning(f"LLM이 '{target} {prop}' 명령을 해석했지만, 유효한 작업이 아닙니다.")
        else:
            st.error("LLM이 명령을 이해하지 못했습니다. 더 명확하게 말씀해주세요.")

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
                <script type="importmap">{{"imports":{{"three":"https://unpkg.com/three@0.160.0/build/three.module.js","three/addons/":"https://unpkg.com/three@0.160.0/examples/jsm/"}}}}</script>
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
