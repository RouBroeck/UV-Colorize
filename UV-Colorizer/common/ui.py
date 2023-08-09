import bpy



class BasePanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "UV Colorizer"


class PalettePanel(BasePanel):
    """Panel to pick a Palette"""

    bl_idname = "UV_COLORIZE_PT_palette_picker"
    bl_label = "Palette Materials"

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        row = layout.row()
        row.template_list("PaletteMatsList", "", bpy.data, "materials", context.window_manager.uv_colorizer, "mat_index")
        column = row.column(align=True)
        column.operator("uv_colorizer.add_material", text="", icon="ADD")
        column.operator("uv_colorizer.del_material", text="", icon="REMOVE")
        column.separator()
        column.operator("uv_colorizer.dup_material", text="", icon="DUPLICATE")
        mat = bpy.data.materials[context.window_manager.uv_colorizer.mat_index]

        node = GetPaletteNode(mat)
        if node:
            fct = "uv_colorizer.dup_image" if node.image else "image.new"
            layout.template_ID(node, "image", new=fct, open="image.open")#fake-user etc. ist doof
        else:
            layout.operator("uv_colorizer.transform_material", text="Transform to Palette")
            return
        

        #Color Picker ggf. Eigenes Panel
        if node.image is None:
            return
        
        box = layout.box()
        row = box.row()
        row.prop(node.image.uv_palette.colors[node.image.uv_palette.index], "color")

        grid = box.grid_flow(row_major = True, even_columns = True, even_rows = True)
        for i,item in enumerate(node.image.uv_palette.colors):
            if item.active: 
                box = grid.column()
                box.alert = True
                box.prop(item, "active", icon_value=item.icon, icon_only=True, emboss=False, index=i)
            else:
                grid.prop(item, "active", icon_value=item.icon, icon_only=True, emboss=False, index=i)



class PaletteMatsList(bpy.types.UIList):
    use_filter_palettes: bpy.props.BoolProperty(name = "Show all Materials")
    use_filter_order_reverse: bpy.props.BoolProperty(name = "Sort by Name")

    def draw_item(self, context: bpy.types.Context, layout:bpy.types.UILayout, data, item:bpy.types.Material, icon, active_data, active_propname):
        layout.prop(item, "name", text="", emboss=False, icon_value=layout.icon(item))
        
        #Grayout unused Materials
        if item.users == 0:
            layout.active = False

        #Mark active Materials
        isActive = False
        if hasattr(context.active_object, "material_slots"):
            for slot in context.active_object.material_slots:
                if slot.material == item:
                    isActive = True
                    break
        if isActive:
            layout.label(text="",icon="CHECKMARK")

    def draw_filter(self, context: bpy.types.Context, layout:bpy.types.UILayout):
        row = layout.row()

        subrow = row.row(align=True)
        subrow.prop(self, "filter_name", text="")

        icon = 'HIDE_OFF' if self.use_filter_palettes else 'HIDE_ON'
        subrow.prop(self, "use_filter_palettes", text="", icon=icon)

        icon = 'TRIA_UP' if self.use_filter_order_reverse else 'TRIA_DOWN'
        subrow.prop(self, "use_filter_order_reverse", text="", icon=icon)

    def filter_items(self, context, data, propname):
        helper_funcs = bpy.types.UI_UL_list

        mats = getattr(data, propname)

        flt_flags = []
        flt_neworder = []

        #Filter by Name
        flt_flags = helper_funcs.filter_items_by_name(self.filter_name, self.bitflag_filter_item, mats, "name")
        if not flt_flags:
            flt_flags = [self.bitflag_filter_item] * len(mats)

        #Filter Pencils
        mat:bpy.types.Material
        for i,mat in enumerate(mats):
            if mat.is_grease_pencil or (not self.use_filter_palettes and GetPaletteNode(mat) is None):
                flt_flags[i] &= ~self.bitflag_filter_item

        #Sort Alphabetically
        flt_neworder = helper_funcs.sort_items_by_name(mats, "name")
        l = len(flt_neworder)

        if self.use_filter_order_reverse:
            for i in range(l // 2):
                flt_neworder[i], flt_neworder[l - i - 1] = flt_neworder[l - i - 1], flt_neworder[i]

        #Used Materials First
        used = set()
        if hasattr(context.active_object, "material_slots"):
            for slot in context.active_object.material_slots:
                if slot.material:
                    used.add(slot.material)

        _sort = [(idx, mat) for idx, mat in enumerate(mats)]
        flt_neworder = helper_funcs.sort_items_helper(_sort, lambda m: m[1] in used, True)

        return flt_flags, flt_neworder


classes = (PalettePanel,PaletteMatsList)

def GetPaletteNode(mat:bpy.types.Material):
    if mat.node_tree is None or mat.node_tree.nodes is None:
        return
    tcs = [ node for node in mat.node_tree.nodes if node.label=="Palette"]
    if len(tcs) > 0:
        return tcs[0]
    else:
        return None


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)