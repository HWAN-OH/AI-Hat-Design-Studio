import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import json
import httpx
import asyncio
import yaml

# --- Page Configuration ---
st.set_page_config(page_title="AI Hat Design Studio", page_icon="👒", layout="wide")

# --- App Title & Description ---
st.title("👒 AI 모자 디자인 스튜디오 v1.3 (Intelligent Engine)")
st.markdown("""
**'Forma'의 두뇌와 손발이 완벽하게 분리되었습니다!**
이제 Forma는 당신의 의도를 깊이 이해하고, 파이썬 코드가 그 지시를 정확하게 실행합니다.
"카우보이 모자로 만들어줘" 라고 다시 한번 명령해보세요.
""")

# --- Session State Initialization ---
if 'hat_config' not in st.session_state:
    st.session_state.hat_config = {"parts": [], "logo_scale": 1.0, "brim_color": "#808080"}

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
async def parse_command_with_llm(command, key, persona):
    if not key:
        st.error("Google AI API Key가 Streamlit Secrets에 등록되지 않았습니다.")
        return None
    
    persona_prompt = f"""
    You are {persona.get('role')}. Your personality is: {persona.get('personality')}.
    Your goal is to translate the user's command into a structured JSON action based on your capabilities and knowledge.
    Your capabilities are: {json.dumps(persona.get('capabilities'))}
    Your knowledge base for styles is: {json.dumps(persona.get('knowledge_base'))}
    Your response MUST be a single, valid JSON object.

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
                st.warning("Google AI API 키가 설정되지 않았습니다.")
            else:
                with st.spinner(f"Forma가 '{command}' 명령을 해석하는 중..."):
                    parsed_command = asyncio.run(parse_command_with_llm(command, api_key, persona_config))
                
                if parsed_command and isinstance(parsed_command, dict):
                    action = parsed_command.get("action")
                    
                    if action == "change_property":
                        # ... (Property change logic)
                        st.success("명령 이해: 속성 변경")
                    elif action == "apply_style":
                        part_changes = parsed_command.get("part_changes", [])
                        st.success(f"명령 이해: '{parsed_command.get('style_name')}' 스타일 적용")
                        
                        # --- FIX: Python code now handles the part lookup ---
                        for change in part_changes:
                            part_type = change.get("part_type")
                            name_contains = change.get("name_contains")
                            
                            if part_type and name_contains:
                                # Find the corresponding model file from the BOM
                                match = bom_df[
                                    (bom_df['part_type'].str.lower() == part_type.lower()) &
                                    (bom_df['name'].str.contains(name_contains, case=False))
                                ]
                                if not match.empty:
                                    new_model = match.iloc[0]['model_file']
                                    # Update the session state
                                    part_found = False
                                    for part in st.session_state.hat_config['parts']:
                                        if part['type'].lower() == part_type.lower():
                                            part['model_file'] = new_model
                                            part_found = True
                                            break
                                    if not part_found:
                                        st.session_state.hat_config['parts'].append({'type': part_type, 'model_file': new_model})
                                    st.info(f"-> {part_type}을(를) {new_model}(으)로 교체합니다.")
                                else:
                                    st.warning(f"BOM에서 '{name_contains}'을(를) 포함하는 {part_type}을(를) 찾을 수 없습니다.")

                    st.rerun()
                else:
                    st.error("LLM이 유효한 명령을 반환하지 못했습니다.")

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
