import bpy
from random import uniform

class palette_picker(bpy.types.Panel):
    bl_idname = "UV_COLORIZE_PT_palette_picker"
    bl_label = "Pick Palette"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, ctx):
        layout = self.layout

        selected = ctx.scene.uv_palettes[ctx.scene.uv_palettes_index]
        layout.template_ID(selected, "img", open="image.open")
        


