import bpy

class PartitionRenderPanel(bpy.types.Panel):
    bl_idname = 'panel.partitionRenderPanel'
    bl_label = 'Partition Render'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'

    def draw(self, context):
        self.layout.operator('render.partition_render', icon = 'RENDER_REGION', text = 'Start/Continue Render')
        self.layout.prop(bpy.context.scene.partition_render_vars, 'xCut')
        self.layout.prop(bpy.context.scene.partition_render_vars, 'yCut')
        self.layout.prop(bpy.context.scene.partition_render_vars, 'useRange')
        row = self.layout.row()
        row.prop(bpy.context.scene.partition_render_vars, 'rangeFrom')
        row.prop(bpy.context.scene.partition_render_vars, 'rangeTo')

def updateUseRange(self, context):
    import PartRender
    PartRender.PartRender.resetPartitions()

def updateXYCut(self, context):
    updateRangeFrom(self, context)
    updateRangeTo(self, context)

def updateRangeFrom(self, context):
    if self.yCut * self.xCut < self.rangeFrom:
        self.rangeFrom = self.xCut * self.yCut
    if self.rangeFrom > self.rangeTo:
        self.rangeTo = self.rangeFrom

def updateRangeTo(self, context):
    if self.yCut * self.xCut < self.rangeTo:
        self.rangeTo = self.xCut * self.yCut
    if self.rangeTo < self.rangeFrom:
        self.rangeFrom = self.rangeTo

class PartitionRenderVariables(bpy.types.PropertyGroup):
    xCut = bpy.props.IntProperty(
        name = 'Blocks By X',
        description = 'X Axis Number Of Blocks',
        subtype='UNSIGNED',
        default = 1,
        min = 1,
        update = updateXYCut
    )
    yCut = bpy.props.IntProperty(
        name = 'Blocks By Y',
        description = 'Y Axis Number Of Blocks',
        subtype='UNSIGNED',
        default = 1,
        min = 1,
        update = updateXYCut
    )
    useRange = bpy.props.BoolProperty(
        name = 'Use Range',
        description = 'Render partitions only from range',
        default = False,
        update = updateUseRange
    )
    rangeFrom = bpy.props.IntProperty(
        name = 'Range From',
        description = 'Start partition from range',
        subtype='UNSIGNED',
        default = 1,
        min = 1,
        update = updateRangeFrom
    )
    rangeTo = bpy.props.IntProperty(
        name = 'Range To',
        description = 'End partition from range',
        subtype='UNSIGNED',
        default = 1,
        min = 1,
        update = updateRangeTo
    )

class PartitionRenderStatic(bpy.types.PropertyGroup):
    tmpFileFormat = bpy.props.StringProperty(
        name = 'Tmp File Format',
        description = 'Temporary file format to store partitions',
        default = 'OPEN_EXR'
    )
    tmpColorMode = bpy.props.StringProperty(
        name = 'Tmp Color Mode',
        description = 'Temporary color mode to store partitions',
        default = 'RGBA'
    )
    tmpFileExtension = bpy.props.StringProperty(
        name = 'Tmp File Extension',
        description = 'Temporary file extension to store partitions',
        default = 'exr'
    )

def register():
    bpy.utils.register_class(PartitionRenderPanel)
    bpy.utils.register_class(PartitionRenderVariables)
    bpy.types.Scene.partition_render_vars = bpy.props.PointerProperty(type = PartitionRenderVariables)
    bpy.utils.register_class(PartitionRenderStatic)
    bpy.types.Scene.partition_render_static = bpy.props.PointerProperty(type = PartitionRenderStatic)

def unregister():
    del bpy.types.Scene.partition_render_vars
    bpy.utils.unregister_class(PartitionRenderStatic)
    bpy.utils.unregister_class(PartitionRenderVariables)
    bpy.utils.unregister_class(PartitionRenderPanel)
