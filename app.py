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
st.title("👒 AI 모자 디자인 스튜디오 MVP v0.2")
st.markdown("""
**BoMi(뇌)**가 최적의 부품을 선택하면, **Forma(손)**가 즉시 3D 모델을 조립합니다.
BOM 데이터를 업로드하고, 부품을 선택한 뒤, '3D 모델 조립하기' 버튼을 눌러 미래를 경험해보세요.
""")

# --- 델타: 시스템의 핵심 로직을 구현합니다 ---

# 1. BoMi: BOM 분석 파트
st.header("Step 1: 'BoMi'에게 부품 선택 지시하기")
uploaded_file = st.file_uploader("BOM 데이터 파일을 업로드하세요 (CSV 또는 Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            bom_df = pd.read_csv(uploaded_file)
        else:
            bom_df = pd.read_excel(uploaded_file)

        bom_df.columns = bom_df.columns.str.strip().str.lower()
        
        st.success("BOM 데이터 로딩 완료!")
        
        # 필터링 인터페이스
        st.subheader("🔍 부품 검색 조건 설정")
        part_types = bom_df['part_type'].unique()
        selected_part_types = st.multiselect("1. 부품 유형 선택:", options=part_types, default=part_types)
        
        materials = bom_df['material'].unique()
        selected_materials = st.multiselect("2. 재질 선택:", options=materials, default=materials)
        
        max_cost = float(bom_df['unit_cost_usd'].max())
        cost_limit = st.slider("3. 부품당 최대 단가 ($):", 0.0, max_cost, max_cost, 0.1)

        # 필터링된 결과
        filtered_df = bom_df[
            (bom_df['part_type'].isin(selected_part_types)) &
            (bom_df['material'].isin(selected_materials)) &
            (bom_df['unit_cost_usd'] <= cost_limit)
        ]

        st.subheader("결과: 'BoMi'가 선택한 부품 리스트")
        st.dataframe(filtered_df)

        # 2. Forma: 3D 조립 파트
        st.markdown("---")
        st.header("Step 2: 'Forma'에게 3D 모델 조립 명령하기")

        if st.button("🚀 3D 모델 조립하기 (Assemble 3D Model)"):
            if filtered_df.empty:
                st.error("조립할 부품이 선택되지 않았습니다. 조건을 다시 설정해주세요.")
            else:
                with st.spinner("'Forma'가 3D 모델을 조립하는 중입니다..."):
                    
                    # GitHub 저장소의 원시 파일 URL을 생성합니다.
                    # 대표님의 GitHub 사용자 이름과 저장소 이름을 정확히 입력해야 합니다.
                    github_user = "HWAN-OH"
                    github_repo = "AI-Hat-Design-Studio" # 대표님께서 만드신 새 저장소 이름
                    base_url = f"https://raw.githubusercontent.com/{github_user}/{github_repo}/main/models/"

                    # 조립할 모델 파일의 전체 URL 리스트를 생성합니다.
                    models_to_load = []
                    for index, row in filtered_df.iterrows():
                        models_to_load.append({
                            "type": row['part_type'],
                            "url": base_url + row['model_file']
                        })
                    
                    # 3D 뷰어를 위한 HTML/JavaScript 코드 생성
                    html_code = f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <title>Forma 3D Viewer</title>
                            <style>
                                body {{ margin: 0; }}
                                canvas {{ display: block; }}
                            </style>
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

                                // 1. 기본 씬, 카메라, 렌더러 설정
                                const scene = new THREE.Scene();
                                scene.background = new THREE.Color(0xf0f2f5);
                                const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
                                camera.position.set(0, 0.1, 0.5);

                                const renderer = new THREE.WebGLRenderer({{ antialias: true }});
                                renderer.setSize(window.innerWidth, window.innerHeight);
                                document.body.appendChild(renderer.domElement);

                                // 2. 조명 설정
                                const ambientLight = new THREE.AmbientLight(0xffffff, 1.5);
                                scene.add(ambientLight);
                                const directionalLight = new THREE.DirectionalLight(0xffffff, 2);
                                directionalLight.position.set(1, 1, 1);
                                scene.add(directionalLight);

                                // 3. 컨트롤 설정 (마우스로 회전/줌)
                                const controls = new OrbitControls(camera, renderer.domElement);
                                controls.enableDamping = true;

                                // 4. Python에서 전달받은 모델 데이터
                                const models = {json.dumps(models_to_load)};
                                const loader = new GLTFLoader();
                                const hatParts = new THREE.Group();
                                scene.add(hatParts);

                                // 5. 모델 로딩 및 조립 로직
                                let loadedCount = 0;
                                models.forEach(modelData => {{
                                    loader.load(modelData.url, (gltf) => {{
                                        const model = gltf.scene;
                                        // 간단한 조립 규칙
                                        if (modelData.type.toLowerCase() === 'crown') {{
                                            // Crown은 중심에 배치
                                        }} else if (modelData.type.toLowerCase() === 'brim') {{
                                            model.position.set(0, 0, 0.1); // 예시: 챙을 약간 앞으로
                                        }} else if (modelData.type.toLowerCase() === 'strap') {{
                                            model.position.set(0, 0, -0.15); // 예시: 스트랩을 약간 뒤로
                                        }}
                                        hatParts.add(model);
                                        
                                        loadedCount++;
                                        // 모든 모델이 로드되면 화면 중앙에 맞춤
                                        if (loadedCount === models.length) {{
                                            const box = new THREE.Box3().setFromObject(hatParts);
                                            const center = box.getCenter(new THREE.Vector3());
                                            hatParts.position.sub(center);
                                        }}
                                    }}, undefined, (error) => {{
                                        console.error('An error happened while loading ' + modelData.url, error);
                                    }});
                                }});

                                // 6. 렌더링 루프
                                function animate() {{
                                    requestAnimationFrame(animate);
                                    controls.update();
                                    renderer.render(scene, camera);
                                }}
                                animate();

                                // 창 크기 변경 시 대응
                                window.addEventListener('resize', () => {{
                                    camera.aspect = window.innerWidth / window.innerHeight;
                                    camera.updateProjectionMatrix();
                                    renderer.setSize(window.innerWidth, window.innerHeight);
                                }});

                            </script>
                        </body>
                        </html>
                    """
                    
                    # Streamlit에 3D 뷰어 컴포넌트 렌더링
                    st.subheader("결과: 'Forma'가 조립한 3D 모델")
                    components.html(html_code, height=600, scrolling=False)

    except Exception as e:
        st.error(f"파일을 처리하는 중 오류가 발생했습니다: {e}")

else:
    st.info("시작하려면 BOM 파일을 업로드해주세요.")
