import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import json
import httpx
import asyncio
import yaml

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Hat Design Studio",
    page_icon="👒",
    layout="wide"
)

# --- App Title & Description ---
st.title("👒 AI 모자 디자인 스튜디오 v1.2 (Persona-Powered)")
st.markdown("""
**'Forma'에게 '페르소나'가 주입되었습니다!**
이제 Forma는 단순한 번역기가 아닌, 모자 스타일에 대한 지식을 가진 'AI 디자이너'로서 당신의 말을 이해합니다.
"카우보이 모자로 바꿔줘" 또는 "로고를 2배 키워줘" 와 같이 자유롭게 명령해보세요.
""")

# --- Session State Initialization ---
if 'hat_config' not in st.session_state:
    st.session_state.hat_config = {
        "parts": [], "logo_scale": 1.0, "brim_color": "#808080"
    }

# --- Data & Persona Loading ---
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
api_key = st.secrets.get("GOOGLE_AI_API_KEY")

# --- LLM Function ---
async def parse_command_with_llm(command, key, persona, available_parts):
    if not key:
        st.error("Google AI API Key가 Streamlit Secrets에 등록되지 않았습니다.")
        return None

    persona_prompt = f"""
    You are {persona.get('role', 'an AI assistant')}. Your personality is: {persona.get('personality', 'helpful')}.
    Your goal is to translate the user's command into a structured JSON action.
    
    You have two main capabilities:
    1. `change_property`: To modify a property like color or scale.
    2. `apply_style`: To change multiple parts at once based on a style name.

    KNOWLEDGE BASE (Styles):
    {json.dumps(persona.get('knowledge_base', []), indent=2)}

    AVAILABLE PARTS:
    {json.dumps(available_parts, indent=2)}

    Based on the user's command, decide which action to take. Your response MUST be a single, valid JSON object.

    EXAMPLES:
    - User: "make the logo 2x bigger" -> {{"action": "change_property", "target": "logo", "property": "scale", "value": 2.0}}
    - User: "I want a cowboy hat" -> {{"action": "apply_style", "style_name": "cowboy hat", "changes": [{{"action": "change_part", "part_type": "Crown", "new_model_file": "crown_fedora.glb"}}, {{"action": "change_part", "part_type": "Brim", "new_model_file": "brim_wide.glb"}}]}}

    Now, parse this command:
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

# --- Main App Logic ---
if bom_df is not None and persona_config is not None:
    st.header("Step 1: 부품 라이브러리")
    st.dataframe(bom_df)

    if st.button("초기 모델 조립", key="initial_assembly"):
        # Load default parts for initial assembly
        initial_parts = bom_df[bom_df['part_type'].isin(['Crown', 'Brim', 'Strap'])]
        parts_to_load = []
        for index, row in initial_parts.iterrows():
            parts_to_load.append({"type": row['part_type'], "model_file": row['model_file']})
        st.session_state.hat_config['parts'] = parts_to_load
        st.success("초기 모델 준비 완료. 아래에 명령을 입력하세요.")

    if st.session_state.hat_config['parts']:
        st.markdown("---")
        st.header("Step 2: 대화형 디자인")
        command = st.text_input("Forma에게 명령하세요 (예: 'make it a cowboy hat')")

        if command:
            if not api_key:
                st.warning("Google AI API 키가 설정되지 않아, LLM 연동이 불가능합니다.")
            else:
                with st.spinner(f"Forma가 '{command}' 명령을 해석하는 중..."):
                    available_parts_list = bom_df.to_dict('records')
                    parsed_command = asyncio.run(parse_command_with_llm(command, api_key, persona_config, available_parts_list))
                
                # --- FIX: Simplified and robust if/else structure ---
                if parsed_command and isinstance(parsed_command, dict):
                    action = parsed_command.get("action")
                    
                    if action == "change_property":
                        target = parsed_command.get("target")
                        prop = parsed_command.get("property")
                        val = parsed_command.get("value")
                        if target == 'logo' and prop == 'scale':
                            st.session_state.hat_config['logo_scale'] = float(val)
                            st.success(f"명령 이해: 로고 스케일 {val}로 변경")
                        elif target == 'brim' and prop == 'color':
                            color_map = {"red": "#ff0000", "blue": "#0000ff", "green": "#008000", "black": "#000000", "gray": "#808080"}
                            st.session_state.hat_config['brim_color'] = color_map.get(str(val).lower(), "#808080")
                            st.success(f"명령 이해: 챙 색상 {val}로 변경")
                        else:
                            st.warning(f"LLM이 '{target} {prop}' 명령을 해석했지만, 유효한 작업이 아닙니다.")

                    elif action == "apply_style":
                        changes = parsed_command.get("changes", [])
                        st.success(f"명령 이해: '{parsed_command.get('style_name')}' 스타일 적용")
                        for change in changes:
                            part_type = change.get("part_type")
                            new_model = change.get("new_model_file")
                            if part_type and new_model:
                                part_found = False
                                for part in st.session_state.hat_config['parts']:
                                    if part['type'].lower() == part_type.lower():
                                        part['model_file'] = new_model
                                        part_found = True
                                        break
                                if not part_found:
                                    st.session_state.hat_config['parts'].append({'type': part_type, 'model_file': new_model})
                                st.info(f"-> {part_type}을(를) {new_model}로 교체합니다.")
                    
                    else:
                        st.warning("LLM이 알 수 없는 액션을 반환했습니다.")

                    st.experimental_rerun()
                else:
                    st.error("LLM이 유효한 명령을 반환하지 못했습니다. 더 명확하게 말씀해주세요.")

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
