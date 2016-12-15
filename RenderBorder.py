import bpy

class RenderBorder(bpy.types.Operator):
    bl_idname = "render.set_render_border"
    bl_label = "Set Render Border"

    x1 = bpy.props.IntProperty(
        subtype = 'UNSIGNED',
        name = "X1",
        description = "Left Top X Coordinate",
        soft_min = 0,
        default = 0
    )
    y1 = bpy.props.IntProperty(
        subtype = 'UNSIGNED',
        name = "Y1",
        description = "Left Top Y Coordinate",
        soft_min = 0,
        default = 0
    )
    x2 = bpy.props.IntProperty(
        subtype = 'UNSIGNED',
        name = "X2",
        description = "Right Bottom X Coordinate",
        soft_min = 0,
        default = 0
    )
    y2 = bpy.props.IntProperty(
        subtype = 'UNSIGNED',
        name = "Y2",
        description = "Right Bottom Y Coordinate",
        soft_min = 0,
        default = 0
    )
    height = bpy.props.IntProperty(
        subtype = 'UNSIGNED',
        name = "Height",
        description = "Height",
        soft_min = 0,
        default = 0
    )
    width = bpy.props.IntProperty(
        subtype = 'UNSIGNED',
        name = "Width",
        description = "Width",
        soft_min = 0,
        default = 0
    )

    def execute(self, context):
        if self.width == 0 and self.height == 0:
            if (self.x1 == self.x2) or (self.y1 == self.y2):
                return {'CANCELLED'}
        elif self.width == 0 or self.height == 0:
            return {'CANCELLED'}
        bpy.context.scene.render.border_min_x = self.x1 / bpy.context.scene.render.resolution_x
        bpy.context.scene.render.border_min_y = 1 - self.y1 / bpy.context.scene.render.resolution_y
        if self.width != 0 and self.height != 0:
            bpy.context.scene.render.border_max_x = (self.x1 + self.width) / bpy.context.scene.render.resolution_x
            bpy.context.scene.render.border_max_y = 1 - (self.y1 + self.height) / bpy.context.scene.render.resolution_y
        else:
            bpy.context.scene.render.border_max_x = self.x2 / bpy.context.scene.render.resolution_x
            bpy.context.scene.render.border_max_y = 1 - self.y2 / bpy.context.scene.render.resolution_y
        if bpy.context.scene.render.border_min_x > bpy.context.scene.render.border_max_x:
            bpy.context.scene.render.border_max_x, bpy.context.scene.render.border_min_x = bpy.context.scene.render.border_min_x, bpy.context.scene.render.border_max_x
        if bpy.context.scene.render.border_min_y > bpy.context.scene.render.border_max_y:
            bpy.context.scene.render.border_max_y, bpy.context.scene.render.border_min_y = bpy.context.scene.render.border_min_y, bpy.context.scene.render.border_max_y
        bpy.context.scene.render.use_border = True
        return {'FINISHED'}


def register():
    bpy.utils.register_class(RenderBorder)

def unregister():
    bpy.utils.unregister_class(RenderBorder)

if __name__ == "__main__":
    register()
