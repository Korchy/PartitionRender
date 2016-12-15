import bpy
import os
import math
import json

class PartRender(bpy.types.Operator):
    bl_idname = 'render.partition_render'
    bl_label = 'Partition Render'
    bl_options = {'REGISTER', 'UNDO'}

    currentPartitionNumber = 0
    dirPath = ''
    infoFile = ''
    timer = None
    windowToRedrawCompositing = bpy.context.window_manager.windows[0].screen.areas[0]
    windowToRedrawCompositingType = 'INFO'

    def execute(self, context):
        # прочитать текущую партицию из файла
        # если файла нет - первая и создать
        self.__class__.dirPath = os.path.dirname(bpy.data.filepath)+os.path.sep+os.path.splitext(os.path.basename(bpy.data.filepath))[0]
        if not os.path.exists(self.__class__.dirPath):
            os.makedirs(self.__class__.dirPath)
        infoFileName = os.path.splitext(os.path.basename(bpy.data.filepath))[0]+'_pr.json'
        self.__class__.infoFile = self.__class__.dirPath + os.path.sep + infoFileName
        if os.path.exists(self.__class__.infoFile):
            with open(self.__class__.infoFile) as partFile:
                jfile = json.load(partFile)
                self.__class__.currentPartitionNumber = jfile['currentPartition']
        else:
            setNextPartition()
        if self.__class__.currentPartitionNumber <= bpy.context.scene.partition_render_vars.xCut * bpy.context.scene.partition_render_vars.yCut:
            # запуск текущей партиции на рендер
            return self.startRenderPartiton(self.__class__.currentPartitionNumber)
        else:
            # окончание рендера
            print('Finished all partitions')
            self.resetPartitions()
            # формирование нода для композитинга - выполняется в модальном режиме, чтобы окно композитинга обновилось
            self.timer = context.window_manager.event_timer_add(time_step = 0.1, window = context.window)
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}

    def modal(self, context, event):
        # modal execution
        self.createCompositingNodes()
        context.window_manager.event_timer_remove(self.timer)
        return {'FINISHED'}

    def startRenderPartiton(self, partitionNumber):
        # Ренднер партиции partitionNumber
        # Установка рамки
        # отсеченные пиксели, чтобы делилось нацело (добавить их к последней партиции в ряду)
        pixelCompX = bpy.context.scene.render.resolution_x % bpy.context.scene.partition_render_vars.xCut
        pixelCompY = bpy.context.scene.render.resolution_y % bpy.context.scene.partition_render_vars.yCut
        # ширина и высота партиции
        partitionWidth = math.floor(bpy.context.scene.render.resolution_x / bpy.context.scene.partition_render_vars.xCut)
        partitionX = partitionWidth * (((partitionNumber - 1) % bpy.context.scene.partition_render_vars.xCut))
        if partitionNumber % bpy.context.scene.partition_render_vars.xCut == 0:
            partitionWidth += pixelCompX
        partitionHeight = math.floor(bpy.context.scene.render.resolution_y / bpy.context.scene.partition_render_vars.yCut)
        partitionY = partitionHeight * (math.ceil(partitionNumber / bpy.context.scene.partition_render_vars.xCut) - 1)
        if partitionNumber > bpy.context.scene.partition_render_vars.xCut * (bpy.context.scene.partition_render_vars.yCut - 1):
            partitionHeight += pixelCompY
        # установить рамку
        bpy.ops.render.set_render_border(x1 = partitionX, y1 = partitionY, width = partitionWidth, height = partitionHeight)
        # начать рендер выделенной партиции
        if onRenderPartitionFinished not in bpy.app.handlers.render_complete:
            bpy.app.handlers.render_complete.append(onRenderPartitionFinished)
        if onRenderPartitionCancel not in bpy.app.handlers.render_cancel:
            bpy.app.handlers.render_cancel.append(onRenderPartitionCancel)
        print('Render partition number ' + str(self.__class__.currentPartitionNumber))
        startRenderStatus = bpy.ops.render.render('INVOKE_DEFAULT')
        if startRenderStatus == {'CANCELLED'}:
            # Иногда по неопнятной причине возвращается {'CANCELLED'} и рендер не начинается
            # В этом случае продолжить на следующем обновлении сцены
            if renderPartition not in bpy.app.handlers.scene_update_post:
                bpy.app.handlers.scene_update_post.append(renderPartition)
            return {'CANCELLED'}
        else:
            return {'FINISHED'}

    def resetPartitions(self):
        self.__class__.currentPartitionNumber = 0
        if self.__class__.infoFile and os.path.exists(self.__class__.infoFile):
            os.remove(self.__class__.infoFile)
        return {'FINISHED'}

    def createCompositingNodes(self):
        # Создать связку нод по партициям в композиторе
        # Окно для перерисовки композитинга
        PartRender.windowToRedrawCompositing = bpy.context.window_manager.windows[0].screen.areas[0]
        PartRender.windowToRedrawCompositingType = bpy.context.window_manager.windows[0].screen.areas[0].type
        # Переключить окно в режим композитинга. Иначе (т.к. окна не обновляются во время выполнения скрипта) не
        # происходит обновления нодов в композитинге. Решение - показать окно композитинга. Аддон должен работать
        # в модальном режиме. После обновления (по событию обновления сцены) можно вернуть окно в прежний режим
        bpy.context.window_manager.windows[0].screen.areas[0].type = 'NODE_EDITOR'
        bpy.context.window_manager.windows[0].screen.areas[0].spaces.active.tree_type = 'CompositorNodeTree'
        # Включить использование нодов
        if not bpy.context.scene.use_nodes:
            bpy.context.scene.use_nodes = True
        # создание группы для нодов
        group = bpy.data.node_groups.new(type = 'CompositorNodeTree', name = 'CombineImages')
        groupInput = group.nodes.new(type = 'NodeGroupInput')
        groupInput.location = (-150, 0)
        group.outputs.new(type = 'NodeSocketColor', name = 'Out')
        groupOutput = group.nodes.new(type = 'NodeGroupOutput')
        groupOutput.location = (500, 100)
        # открыть все сохраненные партиции, создать под них ноды и связать их
        partitionsCount = bpy.context.scene.partition_render_vars.xCut * bpy.context.scene.partition_render_vars.yCut
        for i in range(partitionsCount):
            bpy.ops.image.open(filepath = self.__class__.dirPath + os.path.sep + 'p_' + str(i + 1) + '.' + bpy.context.scene.partition_render_static.tmpFileExtension, directory = self.__class__.dirPath + os.path.sep)
            # Image
            currentImageNode = group.nodes.new(type = 'CompositorNodeImage')
            currentImageNode.image = bpy.data.images['p_' + str(i + 1) + '.' + bpy.context.scene.partition_render_static.tmpFileExtension]
            locatoinX = i * 200
            locationY = i * -100
            currentImageNode.location = (locatoinX, locationY)
            currentImageNode.name = 'p_' + str(i + 1) + '.' + bpy.context.scene.partition_render_static.tmpFileExtension
            # AlphaOver
            if i > 0:
                currentAlphaOverNode = group.nodes.new(type = 'CompositorNodeAlphaOver')
                locatoinX = i * 200 + 200
                locationY = (i - 1) * -100
                currentAlphaOverNode.location = (locatoinX, locationY)
                currentAlphaOverNode.name = 'p_' + str(i) + '_' + str(i + 1) + '.' + bpy.context.scene.partition_render_static.tmpFileExtension
                # связи
                if i == 1:
                    group.links.new(group.nodes['p_' + str(i) + '.' + bpy.context.scene.partition_render_static.tmpFileExtension].outputs['Image'], currentAlphaOverNode.inputs[1])
                else:
                    group.links.new(group.nodes['p_' + str(i - 1) + '_' + str(i) + '.' + bpy.context.scene.partition_render_static.tmpFileExtension].outputs['Image'], currentAlphaOverNode.inputs[1])
                group.links.new(group.nodes['p_' + str(i + 1) + '.' + bpy.context.scene.partition_render_static.tmpFileExtension].outputs['Image'], currentAlphaOverNode.inputs[2])
        # Output
        if partitionsCount == 1:
            group.links.new(group.nodes['p_' + str(partitionsCount) + '.' + bpy.context.scene.partition_render_static.tmpFileExtension].outputs['Image'], groupOutput.inputs['Out'])
        else:
            group.links.new(group.nodes['p_' + str(partitionsCount - 1) + '_' + str(partitionsCount) + '.' + bpy.context.scene.partition_render_static.tmpFileExtension].outputs['Image'], groupOutput.inputs['Out'])
        # добавить построенную связку в группу и в композитинг
        nodesField = bpy.context.scene.node_tree
        groupNode = nodesField.nodes.new(type = 'CompositorNodeGroup')
        groupNode.node_tree = group
        # Последняя связка
        nodesField.links.new(groupNode.outputs['Out'], nodesField.nodes['Composite'].inputs['Image'])
        # вернуть окно
        if returnAreaAfterCompositingRedraw not in bpy.app.handlers.scene_update_post:
            bpy.app.handlers.scene_update_post.append(returnAreaAfterCompositingRedraw)
        return {'FINISHED'}

def returnAreaAfterCompositingRedraw(scene):
    # Возврат окна в предыдущий режим, после показа композитинга для обновления
    bpy.app.handlers.scene_update_post.remove(returnAreaAfterCompositingRedraw)
    bpy.context.window_manager.windows[0].screen.areas[0].type = PartRender.windowToRedrawCompositingType
    return {'FINISHED'}

def onRenderPartitionFinished(scene):
    print('Partition '+str(PartRender.currentPartitionNumber) + ' finished')
    bpy.app.handlers.render_complete.remove(onRenderPartitionFinished)
    bpy.app.handlers.render_cancel.remove(onRenderPartitionCancel)
    # сохранить партицию
    partPath = PartRender.dirPath + os.path.sep + 'p_' + str(PartRender.currentPartitionNumber) + '.' + bpy.context.scene.partition_render_static.tmpFileExtension
    oldFileFormat = bpy.context.scene.render.image_settings.file_format
    oldColorMode = bpy.context.scene.render.image_settings.color_mode
    bpy.context.scene.render.image_settings.file_format = bpy.context.scene.partition_render_static.tmpFileFormat
    bpy.context.scene.render.image_settings.color_mode = bpy.context.scene.partition_render_static.tmpColorMode
    bpy.data.images['Render Result'].save_render(filepath = partPath)
    bpy.context.scene.render.image_settings.file_format = oldFileFormat
    bpy.context.scene.render.image_settings.color_mode = oldColorMode
    # установить номер следующей партиции
    setNextPartition()
    # запустить продолжение обработки
    if renderPartition not in bpy.app.handlers.scene_update_post:
        bpy.app.handlers.scene_update_post.append(renderPartition)
    return {'FINISHED'}

def onRenderPartitionCancel(scene):
    bpy.app.handlers.render_complete.remove(onRenderPartitionFinished)
    bpy.app.handlers.render_cancel.remove(onRenderPartitionCancel)
    print('Canceled on partition number '+str(PartRender.currentPartitionNumber))
    return {'FINISHED'}

def renderPartition(scene):
    if renderPartition in bpy.app.handlers.scene_update_post:
        bpy.app.handlers.scene_update_post.remove(renderPartition)
    # запустить рендер очередной партиции
    return bpy.ops.render.partition_render()

def setNextPartition():
    # установка номера следующей партиции
    PartRender.currentPartitionNumber += 1
    with open(PartRender.infoFile, 'w') as infoFile:
        json.dump({'currentPartition': PartRender.currentPartitionNumber}, infoFile, indent = 4)
    return {'FINISHED'}

def register():
    bpy.utils.register_class(PartRender)

def unregister():
    bpy.utils.unregister_class(PartRender)
