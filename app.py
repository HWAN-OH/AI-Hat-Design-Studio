import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import json

# --- 페이지 기본 설정 ---
st.set_page_config(
    page_title="AI Hat Design Studio",
    page_icon="👒",
    layout="wide"
)

# --- 루미나: 앱의 비전과 사용법을 설명합니다 ---
st.title("👒 AI 모자 디자인 스튜디오 MVP v0.3")
st.markdown("""
**'대화형 디자인'** 기능이 탑재되었습니다.
이제 'Forma'는 당신의 말을 알아듣고, 실시간으로 3D 모델을 수정합니다.
BOM 데이터를 올리고, 초기 모델을 조립한 뒤, 채팅창에 명령을 내려보세요.
""")

# --- 델타: 시스템의 핵심 로직을 구현합니다 ---

# 세션 상태 초기화: 디자인 상태를 기억하기 위함
if 'hat_config' not in st.session_state:
    st.session_state.hat_config = {
        "parts": [],
        "logo_scale": 1.0,
        "brim_color": "#808080" # 기본 색상 (회색)
    }

# 1. BoMi: BOM 분석 파트
st.header("Step 1: 'BoMi' - 부품 선택")
uploaded_file = st.file_uploader("BOM 데이터 파일을 업로드하세요 (CSV)", type=["csv"])

if uploaded_file is not None:
    try:
        bom_df = pd.read_csv(uploaded_file)
        bom_df.columns = bom_df.columns.str.strip().str.lower()
        
        st.subheader("선택된 부품 리스트")
        st.dataframe(bom_df)

        # 초기 모델 조립 버튼
        if st.button("초기 모델 조립하기", key="initial_assembly"):
            with st.spinner("'Forma'가 초기 모델을 조립합니다..."):
                # 선택된 부품 정보를 세션 상태에 저장
                parts_to_load = []
                for index, row in bom_df.iterrows():
                    parts_to_load.append({
                        "type": row['part_type'],
                        "model_file": row['model_file']
                    })
                st.session_state.hat_config['parts'] = parts_to_load
                st.success("초기 모델이 준비되었습니다. 아래 채팅창에 명령을 내려보세요.")

    except Exception as e:
        st.error(f"파일 처리 중 오류: {e}")

# 2. Forma: 3D 조립 및 대화형 수정 파트
if st.session_state.hat_config['parts']:
    st.markdown("---")
    st.header("Step 2: 'Forma' - 대화형 디자인")

    # 자연어 명령 입력창
    command = st.text_input(
        "Forma에게 명령을 내리세요 (예: 'logo scale 1.5' 또는 'brim color red')",
        key="command_input"
    )

    # LLM의 의도 해석 (시뮬레이션)
    if command:
        try:
            parts = command.lower().split()
            if len(parts) == 3:
                target, property, value = parts
                if target == 'logo' and property == 'scale':
                    st.session_state.hat_config['logo_scale'] = float(value)
                    st.success(f"로고 스케일을 {value}로 변경합니다.")
                elif target == 'brim' and property == 'color':
                    # 간단한 색상 이름 -> Hex 코드로 변환
                    color_map = {"red": "#ff0000", "blue": "#0000ff", "green": "#008000", "black": "#000000"}
                    hex_color = color_map.get(value, "#808080")
                    st.session_state.hat_config['brim_color'] = hex_color
                    st.success(f"챙 색상을 {value}로 변경합니다.")
                else:
                    st.warning("이해할 수 없는 명령입니다. (예: 'logo scale 1.5')")
            else:
                st.warning("명령 형식이 올바르지 않습니다. (예: 'target property value')")
        except Exception as e:
            st.error(f"명령 처리 중 오류: {e}")


    # 3D 뷰어 렌더링
    with st.container():
        # GitHub 저장소의 원시 파일 URL 생성
        github_user = "HWAN-OH"
        github_repo = "AI-Hat-Design-Studio"
        base_url = f"https://raw.githubusercontent.com/{github_user}/{github_repo}/main/models/"

        models_to_load = []
        for part in st.session_state.hat_config['parts']:
             models_to_load.append({
                "type": part['type'],
                "url": base_url + part['model_file']
            })

        # 현재 디자인 상태를 JavaScript로 전달
        config_json = json.dumps(st.session_state.hat_config)

        html_code = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style> body {{ margin: 0; }} canvas {{ display: block; }} </style>
            </head>
            <body>
                <script type="importmap">
                    {{
                        "imports": {{
                            "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
                            "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"
                        }}
                    }}
                </script>
                <script type="module">
                    import * as THREE from 'three';
                    import {{ GLTFLoader }} from 'three/addons/loaders/GLTFLoader.js';
                    import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';

                    const scene = new THREE.Scene();
                    scene.background = new THREE.Color(0xf0f2f5);
                    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
                    camera.position.set(0, 0.1, 0.5);

                    const renderer = new THREE.WebGLRenderer({{ antialias: true }});
                    renderer.setSize(window.innerWidth, window.innerHeight);
                    document.body.appendChild(renderer.domElement);

                    const ambientLight = new THREE.AmbientLight(0xffffff, 1.5);
                    scene.add(ambientLight);
                    const directionalLight = new THREE.DirectionalLight(0xffffff, 2);
                    directionalLight.position.set(1, 1, 1);
                    scene.add(directionalLight);

                    const controls = new OrbitControls(camera, renderer.domElement);
                    
                    // Python에서 전달받은 현재 디자인 설정
                    const hatConfig = {config_json};
                    const models = {json.dumps(models_to_load)};
                    const loader = new GLTFLoader();
                    const hatParts = new THREE.Group();
                    scene.add(hatParts);

                    models.forEach(modelData => {{
                        loader.load(modelData.url, (gltf) => {{
                            const model = gltf.scene;
                            
                            // 명령에 따라 모델 속성 변경
                            if (modelData.type.toLowerCase() === 'logo') {{
                                model.scale.setScalar(hatConfig.logo_scale || 1.0);
                            }}
                            if (modelData.type.toLowerCase() === 'brim') {{
                                model.traverse((child) => {{
                                    if (child.isMesh) {{
                                        child.material = child.material.clone();
                                        child.material.color.set(hatConfig.brim_color || "#808080");
                                    }}
                                }});
                            }}
                            
                            hatParts.add(model);
                        }});
                    }});

                    function animate() {{
                        requestAnimationFrame(animate);
                        controls.update();
                        renderer.render(scene, camera);
                    }}
                    animate();
                </script>
            </body>
            </html>
        """
        components.html(html_code, height=600, scrolling=False)
