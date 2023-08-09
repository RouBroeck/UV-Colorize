import bpy

class AddMaterialOperator(bpy.types.Operator):
    bl_idname = "uv_colorizer.add_material"
    bl_label = "Add Palette Material"

    def execute(self, context):
        mat = bpy.data.materials.new("Palette")
        mat.use_nodes=True 
        principled_BSDF = mat.node_tree.nodes.get('Principled BSDF')
        tex_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
        tex_node.label = "Palette"
        tex_node.interpolation = "Closest"

        mat.node_tree.links.new(tex_node.outputs[0], principled_BSDF.inputs[0])

        return {'FINISHED'}
    
class DelMaterialOperator(bpy.types.Operator):
    bl_idname = "uv_colorizer.del_material"
    bl_label = "Delete Palette Material"

    def execute(self, context):
        mat = bpy.data.materials[context.window_manager.uv_colorizer.mat_index]
        context.window_manager.uv_colorizer.mat_index = max(min(context.window_manager.uv_colorizer.mat_index, len(bpy.data.materials)-2), 0)
        bpy.data.materials.remove(mat)
        return {'FINISHED'}
    
class DupMaterialOperator(bpy.types.Operator):
    bl_idname = "uv_colorizer.dup_material"
    bl_label = "Duplicate Palette Material"

    def execute(self, context):
        mat = bpy.data.materials[context.window_manager.uv_colorizer.mat_index].copy()
        for i, m in enumerate(bpy.data.materials):
            if m == mat:
                context.window_manager.uv_colorizer.mat_index = i
                return {'FINISHED'}
        return {'FINISHED'}
    
class DupImageOperator(bpy.types.Operator):
    """Duplicates the selected Image"""
    bl_idname = "uv_colorizer.dup_image"
    bl_label = "Duplicate Image"

    def execute(self, context):
        mat = bpy.data.materials[context.window_manager.uv_colorizer.mat_index]
        ###################################################################Besser als util FKT
        tcs = [ node for node in mat.node_tree.nodes if node.label=="Palette"]
        img = tcs[0].image.copy()
        tcs[0].image = img
        if img.uv_palette:
            img.uv_palette.InitColors(context, img)
        return {'FINISHED'}
    
class TransformMaterialOperator(bpy.types.Operator):
    """Duplicates the selected Image"""
    bl_idname = "uv_colorizer.transform_material"
    bl_label = "Adds a PaletteNode to the Material"

    def execute(self, context):
        mat = bpy.data.materials[context.window_manager.uv_colorizer.mat_index]
        mat.use_nodes=True 
        material_output = mat.node_tree.nodes.get('Material Output')
        principled_BSDF = mat.node_tree.nodes.get('Principled BSDF')
        tex_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
        tex_node.label = "Palette"
        tex_node.interpolation = "Closest"

        mat.node_tree.links.new(tex_node.outputs[0], principled_BSDF.inputs[0])

        return {'FINISHED'}

classes = (AddMaterialOperator, DelMaterialOperator, DupMaterialOperator, DupImageOperator, TransformMaterialOperator)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)