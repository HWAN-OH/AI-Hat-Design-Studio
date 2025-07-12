import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import json
import asyncio
import yaml
from forma_engine import parse_command_with_llm # Import the engine

# --- Page Configuration & Title ---
st.set_page_config(page_title="AI Hat Design Studio", page_icon="👒", layout="wide")
st.title("👒 AI 모자 디자인 스튜디오 v2.1 (Stable Engine)")
st.markdown("이제 **Forma 엔진**과의 통신 프로토콜이 완벽해졌습니다. 시스템은 더 안정적으로 작동합니다.")

# --- Session State & Asset Loading ---
if 'hat_config' not in st.session_state:
    st.session_state.hat_config = {"parts": [], "logo_scale": 1.0, "brim_color": "#808080"}

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
    st.header("Step 1: 부품 라이브러리 (BOM)")
    st.dataframe(bom_df)

    if st.button("초기 모델 조립", key="initial_assembly"):
        initial_parts = bom_df[bom_df['part_type'].isin(['Crown', 'Brim', 'Strap'])]
        st.session_state.hat_config['parts'] = [{"type": row['part_type'], "model_file": row['model_file']} for index, row in initial_parts.iterrows()]
        st.success("초기 모델 준비 완료. 아래에 명령을 입력하세요.")

    if st.session_state.hat_config['parts']:
        st.markdown("---")
        st.header("Step 2: 대화형 디자인")
        command = st.text_input("Forma에게 명령하세요 (예: 'make it a cowboy hat')")

        if command:
            if not api_key:
                st.warning("Google AI API 키가 설정되지 않았습니다.")
            else:
                with st.spinner(f"Forma 엔진이 '{command}' 명령을 해석하는 중..."):
                    # --- FIX: Pass the 'available_parts' data to the engine ---
                    available_parts_list = bom_df.to_dict('records')
                    parsed_command = asyncio.run(parse_command_with_llm(command, api_key, persona_config, available_parts_list))
                    # --- END OF FIX ---
                
                if parsed_command and "error" not in parsed_command:
                    action = parsed_command.get("action")
                    if action == "apply_style":
                        part_changes = parsed_command.get("part_changes", [])
                        st.success(f"명령 이해: '{parsed_command.get('style_name')}' 스타일 적용")
                        for change in part_changes:
                            part_type = change.get("part_type")
                            name_contains = change.get("name_contains")
                            if part_type and name_contains:
                                match = bom_df[(bom_df['part_type'].str.lower() == part_type.lower()) & (bom_df['name'].str.contains(name_contains, case=False))]
                                if not match.empty:
                                    new_model = match.iloc[0]['model_file']
                                    for part in st.session_state.hat_config['parts']:
                                        if part['type'].lower() == part_type.lower():
                                            part['model_file'] = new_model
                                            break
                                    st.info(f"-> {part_type}을(를) {new_model}(으)로 교체합니다.")
                    # Add other actions like 'change_property' here
                    st.rerun()
                else:
                    st.error(f"LLM이 명령을 처리하지 못했습니다: {parsed_command.get('error', 'Unknown error')}")

        # 3D Viewer Rendering Logic
        with st.container():
            github_user = "HWAN-OH"
            github_repo = "AI-Hat-Design-Studio"
            base_url = f"https://raw.githubusercontent.com/{github_user}/{github_repo}/main/models/"
            models_to_load = [{"type": part['type'], "url": base_url + part['model_file']} for part in st.session_state.hat_config['parts']]
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
