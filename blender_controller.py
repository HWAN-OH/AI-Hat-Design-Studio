import pandas as pd

def generate_blender_script(design_plan, bom_df):
    """
    Generates a Python script for Blender based on the design plan.
    This version includes a more robust context override to prevent view3d errors.
    """
    
    # Script Header
    script_lines = [
        "import bpy",
        "import os",
        "",
        "# --- Clear existing mesh objects ---",
        "if bpy.context.active_object and bpy.context.active_object.mode != 'OBJECT':",
        "    bpy.ops.object.mode_set(mode='OBJECT')",
        "bpy.ops.object.select_all(action='DESELECT')",
        "bpy.ops.object.select_by_type(type='MESH')",
        "bpy.ops.object.delete()",
        "",
        "# --- Set up model directory ---",
        "# Please place your 3D models in a 'models' subfolder",
        "# and run this script from Blender's Text Editor.",
        "try:",
        "    script_dir = os.path.dirname(bpy.data.filepath)",
        "except AttributeError:",
        "    # If the blend file is not saved, this will fail.",
        "    # Fallback to a relative path, assuming the script is run from the project root.",
        "    script_dir = ''",
        "model_dir = os.path.join(script_dir, 'models')",
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

    # --- FINAL FIX: A more robust method to find and override context ---
    script_lines.extend([
        "",
        "# --- Fit view to all objects with robust context override ---",
        "def get_3d_view_context():",
        "    # Iterate through all windows, screens, and areas to find a 3D Viewport",
        "    for window in bpy.context.window_manager.windows:",
        "        for area in window.screen.areas:",
        "            if area.type == 'VIEW_3D':",
        "                for region in area.regions:",
        "                    if region.type == 'WINDOW':",
        "                        # Found a valid 3D Viewport, return its context",
        "                        return {'window': window, 'screen': window.screen, 'area': area, 'region': region}",
        "    return None",
        "",
        "context_3d = get_3d_view_context()",
        "if context_3d:",
        "    # Execute operators within the found context",
        "    with bpy.context.temp_override(**context_3d):",
        "        bpy.ops.object.select_all(action='SELECT')",
        "        bpy.ops.view3d.view_all(center=False)",
        "        bpy.ops.object.select_all(action='DESELECT')",
        "else:",
        "    print('Could not find a 3D Viewport to adjust the view. Please ensure a 3D Viewport is visible.')"
    ])
    # --- END OF FINAL FIX ---

    return "\n".join(script_lines)
