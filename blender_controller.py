import pandas as pd

def generate_blender_script(design_plan, bom_df):
    """
    Generates a Python script for Blender based on the design plan.
    디자인 계획에 따라 Blender에서 실행할 Python 스크립트를 생성합니다.
    """
    
    # Script Header
    script_lines = [
        "import bpy",
        "import os",
        "",
        "# --- Clear existing mesh objects ---",
        "bpy.ops.object.select_all(action='DESELECT')",
        "bpy.ops.object.select_by_type(type='MESH')",
        "bpy.ops.object.delete()",
        "",
        "# --- Set up model directory ---",
        "# Please place your 3D models in a 'models' subfolder",
        "script_dir = os.path.dirname(os.path.realpath(__file__))",
        "model_dir = os.path.join(script_dir, 'models')",
        "",
    ]

    # Action processing
    actions = design_plan.get("actions", [])
    for i, action in enumerate(actions):
        if action.get("action") == "load_and_place":
            part_name = action.get("part_name")
            
            # Find the model file from BOM
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

    # Script Footer
    script_lines.append("# --- Fit view to all objects ---")
    script_lines.append("bpy.ops.object.select_all(action='SELECT')")
    script_lines.append("bpy.ops.view3d.view_all(center=False)")
    script_lines.append("bpy.ops.object.select_all(action='DESELECT')")

    return "\n".join(script_lines)
