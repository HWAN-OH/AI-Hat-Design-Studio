import pandas as pd

def generate_blender_script(design_plan, bom_df):
    """
    Generates a Python script for Blender using a raw string for the path
    to ensure Windows path compatibility.
    """
    
    # Script Header
    script_lines = [
        "import bpy",
        "import os",
        "from mathutils import Vector",
        "",
        "# ====================================================================",
        "# !!! IMPORTANT: Please replace the path below with YOUR project path !!!",
        "# Example (Windows): r'C:\\Users\\YourName\\Documents\\AI-Hat-Design-Studio'",
        "# The 'r' before the string is crucial. Just copy and paste your path.",
        "# ====================================================================",
        "PROJECT_ROOT_PATH = r'REPLACE_WITH_YOUR_ABSOLUTE_PROJECT_PATH'",
        "",
        "if 'REPLACE_WITH_YOUR_ABSOLUTE_PROJECT_PATH' in PROJECT_ROOT_PATH:",
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
        "bpy.context.view_layer.update()",
        "bpy.ops.object.select_all(action='SELECT')",
        "if bpy.context.selected_objects:",
        "    bpy.ops.view3d.view_all()",
        "bpy.ops.object.select_all(action='DESELECT')",
        "print('Script finished.')"
    ])

    return "\n".join(script_lines)
