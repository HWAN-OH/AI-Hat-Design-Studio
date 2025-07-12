import pandas as pd

def generate_blender_script(design_plan, bom_df):
    """
    Generates a robust Python script for Blender that directly manipulates the view,
    avoiding context-sensitive operators.
    """
    
    # Script Header
    script_lines = [
        "import bpy",
        "import os",
        "from mathutils import Vector",
        "",
        "# --- Clear existing mesh objects ---",
        "if bpy.context.active_object and bpy.context.active_object.mode != 'OBJECT':",
        "    bpy.ops.object.mode_set(mode='OBJECT')",
        "bpy.ops.object.select_all(action='DESELECT')",
        "bpy.ops.object.select_by_type(type='MESH')",
        "bpy.ops.object.delete()",
        "",
        "# --- Set up model directory ---",
        "try:",
        "    script_dir = os.path.dirname(bpy.data.filepath)",
        "except AttributeError:",
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

    # --- FINAL, ROBUST FIX: Direct view manipulation ---
    script_lines.extend([
        "",
        "bpy.context.view_layer.update()",
        "",
        "def frame_all():",
        "    # Find the 3D view area",
        "    area = next((a for a in bpy.context.screen.areas if a.type == 'VIEW_3D'), None)",
        "    if not area:",
        "        print('No 3D Viewport found.')",
        "        return",
        "",
        "    # Get the 3D view region",
        "    region = next((r for r in area.regions if r.type == 'WINDOW'), None)",
        "    if not region:",
        "        return",
        "",
        "    # Get all visible mesh objects in the scene",
        "    visible_objects = [obj for obj in bpy.context.visible_objects if obj.type == 'MESH']",
        "    if not visible_objects:",
        "        return",
        "",
        "    # Calculate the bounding box of all objects",
        "    min_coord = Vector((float('inf'), float('inf'), float('inf')))",
        "    max_coord = Vector((float('-inf'), float('-inf'), float('-inf')))",
        "",
        "    for obj in visible_objects:",
        "        for corner in obj.bound_box:",
        "            world_corner = obj.matrix_world @ Vector(corner)",
        "            min_coord.x = min(min_coord.x, world_corner.x)",
        "            min_coord.y = min(min_coord.y, world_corner.y)",
        "            min_coord.z = min(min_coord.z, world_corner.z)",
        "            max_coord.x = max(max_coord.x, world_corner.x)",
        "            max_coord.y = max(max_coord.y, world_corner.y)",
        "            max_coord.z = max(max_coord.z, world_corner.z)",
        "",
        "    # Calculate center and size of the bounding box",
        "    center = (min_coord + max_coord) / 2.0",
        "    size = max((max_coord - min_coord).x, (max_coord - min_coord).y, (max_coord - min_coord).z)",
        "",
        "    # Override the context and set the view",
        "    override = {'area': area, 'region': region}",
        "    with bpy.context.temp_override(**override):",
        "        space = area.spaces.active",
        "        space.region_3d.view_location = center",
        "        space.region_3d.view_distance = size * 2.0 # Adjust multiplier for better framing",
        "        space.region_3d.view_rotation = Vector((1, 0, 0, 0)).to_quaternion() # Reset rotation",
        "",
        "frame_all()",
        "print('Script finished.')"
    ])
    # --- END OF FINAL FIX ---

    return "\n".join(script_lines)
