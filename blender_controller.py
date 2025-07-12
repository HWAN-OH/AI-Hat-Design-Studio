import pandas as pd

def generate_blender_script(design_plan, bom_df):
    """
    Generates a Python script for Blender using an absolute path for reliability.
    안정성을 위해 절대 경로를 사용하는 Blender용 Python 스크립트를 생성합니다.
    """
    
    # --- IMPORTANT: User Action Required ---
    # 사용자가 직접 수정해야 할 부분
    script_lines = [
        "import bpy",
        "import os",
        "",
        "# ====================================================================",
        "# !!! 중요: 아래 경로를 당신의 실제 프로젝트 폴더 경로로 수정하세요 !!!",
        "# 예시: 'C:/Users/YourName/Documents/AI-Hat-Design-Studio'",
        "PROJECT_ROOT_PATH = 'REPLACE_WITH_YOUR_ABSOLUTE_PROJECT_PATH'",
        "# ====================================================================",
        "",
        "if PROJECT_ROOT_PATH == 'REPLACE_WITH_YOUR_ABSOLUTE_PROJECT_PATH':",
        "    raise Exception('Please set the PROJECT_ROOT_PATH variable in this script first.')",
        "",
        "# --- Clear existing mesh objects ---",
        "if bpy.context.active_object and bpy.context.active_object.mode != 'OBJECT':",
        "    bpy.ops.object.mode_set(mode='OBJECT')",
        "bpy.ops.object.select_all(action='DESELECT')",
        "bpy.ops.object.select_by_type(type='MESH')",
        "bpy.ops.object.delete()",
        "",
        "# --- Set up model directory ---",
        "model_dir = os.path.join(PROJECT_ROOT_PATH, 'models')",
        "",
    ]

    # Action processing
    actions = design_plan.get("actions", [])
    for i, action in enumerate(actions):
        if action.get("action") == "load_and_place":
            part_name = action.get("part_name")
            
            part_info = bom_df[bom_df['name'].str.contains(part_name, case=False)]
            if not part_info.empty:
                model_file = part_info.iloc[0]['model_file']
                
                script_lines.append(f"# --- Action {i+1}: Load {part_name} ---")
                script_lines.append(f"model_path = os.path.join(model_dir, '{model_file}')")
                script_lines.append(f"if os.path.exists(model_path):")
                script_lines.append(f"    bpy.ops.import_scene.gltf(filepath=model_path)")
                script_lines.append(f"else:")
                script_lines.append(f"    print(f'Warning: Model file not found for {part_name} at {{model_path}}')")
                script_lines.append("")

    # Context override for view_all operator
    script_lines.extend([
        "",
        "# --- Fit view to all objects ---",
        "def get_3d_view_context():",
        "    for window in bpy.context.window_manager.windows:",
        "        for area in window.screen.areas:",
        "            if area.type == 'VIEW_3D':",
        "                for region in area.regions:",
        "                    if region.type == 'WINDOW':",
        "                        return {'window': window, 'screen': window.screen, 'area': area, 'region': region}",
        "    return None",
        "",
        "context_3d = get_3d_view_context()",
        "if context_3d:",
        "    with bpy.context.temp_override(**context_3d):",
        "        bpy.ops.object.select_all(action='SELECT')",
        "        bpy.ops.view3d.view_all(center=False)",
        "        bpy.ops.object.select_all(action='DESELECT')",
        "else:",
        "    print('Could not find a 3D Viewport to adjust the view.')"
    ])

    return "\n".join(script_lines)
