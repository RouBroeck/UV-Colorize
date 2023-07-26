import bpy
import bmesh
from random import uniform
from .uv_colorize_palette_picker import palette_picker

class colorize_panel(bpy.types.Panel):
    bl_idname = "UV_COLORIZE_PT_panel"
    bl_label = "Palettes"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "UV Colorize"

    def draw(self, ctx):
        layout = self.layout

        layout.template_list("UV_COLORIZE_UL_palette_list", "", ctx.scene, "uv_palettes", ctx.scene, "uv_palettes_index")

        row = layout.row()
        row.operator(UV_COLORIZE_OT_add_palette_operator.bl_idname, text="+")
        row.operator(UV_COLORIZE_OT_remove_palette_operator.bl_idname, text="-")

        row = layout.row()
        row.prop(ctx.scene, "uv_palettes_drawing", toggle=True)

        palette = getCurrentPalette()
        if palette and len(palette.colors) > 0:
            box = layout.box()
            grid = box.grid_flow(row_major = True, even_columns = True, even_rows = True)
            for i,item in enumerate(palette.colors):
                grid.prop(item, "active", icon_value=item.icon, icon_only=True, emboss=False, index=i, expand=False)

class UV_COLORIZE_UL_palette_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if getCurrentPalette() == item:
            if item.img:
                layout.popover(palette_picker.bl_idname, text='', translate=True, icon_value=layout.icon(item.material))
            else:
                layout.popover(palette_picker.bl_idname, text='', translate=True, icon="ERROR")
        else:
            if item.img:
                layout.label(text="", icon_value=layout.icon(item.material))
            else:
                layout.label(text="", icon="ERROR")

        layout.prop(item.material, "name", text="", emboss=False)
            
            


class UV_COLORIZE_OT_add_palette_operator(bpy.types.Operator):
    bl_idname = "uv_colorize.add_palette"
    bl_label = "Add UV Palette"

    def execute(self, ctx):
        palette = ctx.scene.uv_palettes.add()
        current = getCurrentPalette()
        if current and current.material:
            palette.material = current.material.copy()
            palette.img = current.img
            ctx.scene.uv_palettes_index = len(ctx.scene.uv_palettes)-1
            updatePalette(self, ctx)
            palette.name = palette.material.name

            return {'FINISHED'}
        
        material = bpy.data.materials.new(name=f"Palette.{len(ctx.scene.uv_palettes):03}")
        material.use_nodes = True
        nodes = material.node_tree.nodes
        nodes.clear()

        node_principled = nodes.new(type='ShaderNodeBsdfPrincipled')
        node_principled.inputs[9].default_value = 1

        node_tex = nodes.new('ShaderNodeTexImage')
        node_tex.name = "Palette"
        node_tex.interpolation = "Closest"
        node_output = nodes.new(type='ShaderNodeOutputMaterial')

        node_principled.location = 0,0
        node_tex.location = -400,0
        node_output.location = 400,0

        links = material.node_tree.links
        link = links.new(node_tex.outputs["Color"], node_principled.inputs["Base Color"])
        link = links.new(node_principled.outputs["BSDF"], node_output.inputs["Surface"])

        palette.material = material
        palette.name = material.name

        ctx.scene.uv_palettes_index = len(ctx.scene.uv_palettes)-1
        return {'FINISHED'}
    
class UV_COLORIZE_OT_remove_palette_operator(bpy.types.Operator):
    bl_idname = "uv_colorize.remove_palette"
    bl_label = "Remove UV Palette"

    def execute(self, ctx):
        if len(ctx.scene.uv_palettes) > 0: 
            bpy.data.materials.remove(getCurrentPalette().material)
            ctx.scene.uv_palettes.remove(ctx.scene.uv_palettes_index)
            ctx.scene.uv_palettes_index = max(min(ctx.scene.uv_palettes_index, len(ctx.scene.uv_palettes)-1), 0)
        return {'FINISHED'}



preview_collections = {}

def updatePalette(self, context):
    palette = getCurrentPalette()
    palette.colors.clear()

    img = palette.img
    if not img:
        return
    width = img.size[0]
    height = img.size[1]
    if width * height > 256:
        Error("Too many colors")
        getCurrentPalette().img = None
        return
    if width*height <= 0:
        Error("Too few colors")
        getCurrentPalette().img = None
        return
    
    palette.material.node_tree.nodes["Palette"].image = img

    pcoll = preview_collections.get(img.name)
    create_new = True
    if pcoll:
        create_new = False
    else:
        pcoll = bpy.utils.previews.new()

    for i in range(width * height):
        color_name = str(i)
        size = 1,1
        index = i * 4
        color = [
            img.pixels[index], # RED
            img.pixels[index + 1], # GREEN
            img.pixels[index + 2], # BLUE
            img.pixels[index + 3] # ALPHA
        ]
        pixels = [*color] * size[0] * size[1]

        icon = pcoll.get(str(i))
        if create_new:
            icon = pcoll.new(str(i))
            icon.icon_size = size
            icon.is_icon_custom = True
            icon.icon_pixels_float = pixels

        color_item = palette.colors.add()
        color_item.name = color_name
        color_item.color = color
        color_item.icon = pcoll[color_name].icon_id
        uv_x = 1/width * (i % width) + 0.5/width
        uv_y = 1./height * (i/width) + 0.5/height
        color_item.uv = [uv_x, uv_y]
        
        uv_x = 1/width * (i % width) + 0.5/width
        uv_y = 1./height * (i/width) + 0.5/height
        color_item.uv = [uv_x, uv_y]
    preview_collections[img.name] = pcoll


def click(self, context):
    if self.active:
        palette = getCurrentPalette()
        for i, c in enumerate(palette.colors):
            if c == self:
                palette.index = i
            else:
                c.active = False

    if bpy.context.object.mode == "EDIT":
        for obj in bpy.context.selected_objects:
            me = obj.data
            bm = bmesh.from_edit_mesh(me)
            uv_lay = bm.loops.layers.uv.active

            mat = getCurrentPalette().material
            faces = []
            for face in bm.faces:
                if face.select:
                    faces.append(face)
            if len(faces) == 0:
                continue
                
            mat_index = -1
            #Add Material if nessesary
            for i, slot in enumerate(obj.material_slots):
                if slot.material == mat:
                    mat_index = i
                    break
            if mat_index == -1:
                obj.data.materials.append(mat)
                mat_index = len(obj.material_slots)
            #Change UV of faces
            for face in faces:
                face.material_index = mat_index
                for loop in face.loops:
                    loop[uv_lay].uv = self.uv
            bm.select_flush(True)
            bmesh.update_edit_mesh(obj.data)

class UV_COLORIZE_UV_palette_color(bpy.types.PropertyGroup):
    active: bpy.props.BoolProperty(name="Active", update=click)
    color: bpy.props.FloatVectorProperty(name="Color", min=0, max=1, subtype="COLOR", size=4, default=(1,1,1,1))
    uv: bpy.props.FloatVectorProperty(name="UV Offset", size=2)
    icon: bpy.props.IntProperty(name="Icon")

class UV_COLORIZE_UV_palette(bpy.types.PropertyGroup):
    colors: bpy.props.CollectionProperty(name="Colors", type=UV_COLORIZE_UV_palette_color)
    material: bpy.props.PointerProperty(name="Material", type=bpy.types.Material)
    img: bpy.props.PointerProperty(name="Source", type=bpy.types.Image, update=updatePalette)
    preview: None
    index: bpy.props.IntProperty(name="index")



def register():
    setattr(bpy.types.Scene, "uv_palettes", bpy.props.CollectionProperty(name="UV Palettes", type=UV_COLORIZE_UV_palette))
    setattr(bpy.types.Scene, "uv_palettes_index", bpy.props.IntProperty(name="UV Palettes index"))
    setattr(bpy.types.Scene, "uv_palettes_drawing", bpy.props.BoolProperty(name="UV Palettes drawing", update= toggleDrawing))



#UTILS
def toggleDrawing(self, context):
    if self.uv_palettes_drawing:
        bpy.ops.object.modal_operator('INVOKE_DEFAULT')

def getCurrentPalette():
    if len(bpy.context.scene.uv_palettes) > bpy.context.scene.uv_palettes_index:
        return bpy.context.scene.uv_palettes[bpy.context.scene.uv_palettes_index]
    else:
        return None

ErrorMsg = None
def Error(reason):
    global ErrorMsg
    ErrorMsg = reason
    bpy.context.window_manager.popup_menu(ErrorPanel, title="Error", icon='ERROR')

def ErrorPanel(self, context):
    self.layout.label(text = ErrorMsg)