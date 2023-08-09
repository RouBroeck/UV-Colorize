import bpy
import bpy.utils.previews
import bmesh

def GetCurrentImage() -> bpy.types.Image:
    mat = bpy.data.materials[bpy.context.window_manager.uv_colorizer.mat_index]
    tcs = [ node for node in mat.node_tree.nodes if node.label=="Palette"]
    if len(tcs) == 0:
        return None
    img:bpy.types.Image = tcs[0].image
    return img


class PaletteColor(bpy.types.PropertyGroup):
    def UpdateColor(self, context):
        img = GetCurrentImage()
        h = hash(img)
        pcoll = preview_collections.get(h)
        if pcoll is None:
            return
        #update Icon Preview
        k = None
        for k in pcoll:
            color = pcoll[k]
            if color.icon_id == self.icon:
                color.icon_pixels_float = self.color
                break
        #update Source Image
        i = int(k) * 4
        img.pixels[i:i+4] = self.color

    def UpdateActive(self, context:bpy.types.Context):
        if self.active:
            mat = bpy.data.materials[context.window_manager.uv_colorizer.mat_index]
            img = GetCurrentImage()

            palette = img.uv_palette
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
                            loop[uv_lay].uv = self.uv_offset
                    bm.select_flush(True)
                    bmesh.update_edit_mesh(obj.data)

    active: bpy.props.BoolProperty(name="Active", update=UpdateActive)
    color: bpy.props.FloatVectorProperty(name="Color", min=0, max=1, subtype="COLOR", size=4, default=(1,1,1,1), update=UpdateColor)
    uv_offset: bpy.props.FloatVectorProperty(name="UV Offset", size=2)
    icon: bpy.props.IntProperty(name="Icon")

preview_collections = {}

class PaletteImgProps(bpy.types.PropertyGroup):

    def InitColors(self, context, img:bpy.types.Image):
        self.colors.clear()
        img.pack()

        width = img.size[0]
        height = img.size[1]
        h = hash(img)
        pcoll = preview_collections.get(h)

        if pcoll is not None:
            print("Load")
            pcoll.clear()
        else:
            print("Create")
            pcoll = bpy.utils.previews.new()
        preview_collections[h] = pcoll

        for i in range(width * height):
            color_name = str(i)
            index = i * 4
            color = [
                img.pixels[index], # RED
                img.pixels[index + 1], # GREEN
                img.pixels[index + 2], # BLUE
                img.pixels[index + 3] # ALPHA
            ]
            icon = pcoll.new(str(i))
            icon.icon_size = 1,1
            icon.is_icon_custom = True

            color_item = self.colors.add()
            color_item.name = color_name
            color_item.icon = pcoll[color_name].icon_id

            uv_x = 1/width * (i % width) + 0.5/width
            uv_y = 1./height * (i/width) + 0.5/height
            color_item.uv_offset = [uv_x, uv_y]

            color_item.color = color
            

    
    colors: bpy.props.CollectionProperty(type=PaletteColor)
    index: bpy.props.IntProperty()


class UVColorizerSettings(bpy.types.PropertyGroup):
    def UpdateIndex(self, context:bpy.types.Context):
        mat = bpy.data.materials[self.mat_index]
        img = GetCurrentImage()
        if img and img.uv_palette:
            img.uv_palette.InitColors(context, img)#Ich glaube kontext kann auch img sein

    mat_index: bpy.props.IntProperty(name="Current Palette Material", update=UpdateIndex)
    mat_filter: bpy.props.BoolProperty(name="Filter Palettes")

classes = (PaletteColor, PaletteImgProps, UVColorizerSettings)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.WindowManager.uv_colorizer = bpy.props.PointerProperty(type=UVColorizerSettings)
    bpy.types.Image.uv_palette = bpy.props.PointerProperty(type=PaletteImgProps)

def unregister():
    del bpy.types.Image.uv_palette
    del bpy.types.WindowManager.uv_colorizer

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)