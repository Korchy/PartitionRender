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
    oldFileFormat = ''
    oldColorMode = ''
    executing = False

    def execute(self, context):
        # прочитать текущую партицию из файла
        self.__class__.executing = True
        self.clearCompositingNodes()
        self.getPartitionNumberToRender()
        if not self.checkFinish():
            # запуск текущей партиции на рендер
            return self.startRenderPartiton(self.__class__.currentPartitionNumber)
        else:
            # окончание рендера
            print('Finished all partitions')
            self.__class__.executing = False
            self.reset()
            # формирование нода для композитинга - выполняется в модальном режиме, чтобы окно композитинга обновилось
            self.timer = context.window_manager.event_timer_add(time_step = 0.1, window = context.window)
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}

    def modal(self, context, event):
        # modal execution
        self.createCompositingNodes()
        context.window_manager.event_timer_remove(self.timer)
        self.reset()
        return {'FINISHED'}

    def getPartitionNumberToRender(self):
        # получение номера партиции для рендера
        self.getInfoFileName()
        if self.__class__.currentPartitionNumber == 0:
            # если файла нет - первая и создать
            if os.path.exists(self.__class__.infoFile):
                with open(self.__class__.infoFile) as currentFile:
                    jsonData = json.load(currentFile)
                    self.__class__.currentPartitionNumber = jsonData['currentPartition']
                    if bpy.context.scene.partition_render_vars.useRange:
                        if self.__class__.currentPartitionNumber > bpy.context.scene.partition_render_vars.rangeTo \
                                or self.__class__.currentPartitionNumber < bpy.context.scene.partition_render_vars.rangeFrom:
                            self.__class__.currentPartitionNumber = bpy.context.scene.partition_render_vars.rangeFrom - 1
                            setNextPartition()
            else:
                setNextPartition()
        # проверить по диапазону
        if bpy.context.scene.partition_render_vars.useRange:
            if self.__class__.currentPartitionNumber < bpy.context.scene.partition_render_vars.rangeFrom:
                self.__class__.currentPartitionNumber = bpy.context.scene.partition_render_vars.rangeFrom - 1
                setNextPartition()

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
            # В этом случае повторить на следующем обновлении сцены
            if renderPartition not in bpy.app.handlers.scene_update_post:
                bpy.app.handlers.scene_update_post.append(renderPartition)
            return {'CANCELLED'}
        else:
            return {'FINISHED'}

    @classmethod
    def savePartitionToFile(cls):
        # сохранить партицию во временный файл
        if cls.dirPath:
            partPath = cls.dirPath + os.path.sep + 'p_' + str(cls.currentPartitionNumber) + '.' + bpy.context.scene.partition_render_static.tmpFileExtension
            cls.oldFileFormat = bpy.context.scene.render.image_settings.file_format
            cls.oldColorMode = bpy.context.scene.render.image_settings.color_mode
            bpy.context.scene.render.image_settings.file_format = bpy.context.scene.partition_render_static.tmpFileFormat
            bpy.context.scene.render.image_settings.color_mode = bpy.context.scene.partition_render_static.tmpColorMode
            # bpy.data.images['Render Result'].save_render(filepath = partPath)
            for currentArea in bpy.context.window_manager.windows[0].screen.areas:
                if currentArea.type == 'IMAGE_EDITOR':
                    overrideArea = bpy.context.copy()
                    overrideArea['area'] = currentArea
                    bpy.ops.image.save_as(overrideArea, copy = True, filepath = partPath)
                    break
            bpy.context.scene.render.image_settings.file_format = cls.oldFileFormat
            bpy.context.scene.render.image_settings.color_mode = cls.oldColorMode
        return {'FINISHED'}

    @classmethod
    def reset(cls):
        cls.getInfoFileName()
        cls.currentPartitionNumber = 0
        if cls.infoFile and os.path.exists(cls.infoFile):
            os.remove(cls.infoFile)
        if bpy.context.scene.render.use_border:
            bpy.context.scene.render.use_border = False
        return {'FINISHED'}

    @classmethod
    def clear(cls):
        cls.reset()
        if cls.dirPath and os.path.exists(cls.dirPath):
            for currentFile in os.listdir(cls.dirPath):
                os.remove(cls.dirPath + os.sep + currentFile)
            os.rmdir(cls.dirPath)
        cls.dirPath = ''
        cls.infoFile = ''
        return {'FINISHED'}

    def createCompositingNodes(self):
        # Создать связку нод по партициям в композиторе
        # Окно для перерисовки композитинга
        PartRender.windowToRedrawCompositing = bpy.context.window_manager.windows[0].screen.areas[0]
        PartRender.windowToRedrawCompositingType = bpy.context.window_manager.windows[0].screen.areas[0].type
        # Переключить окно в режим композитинга. Иначе (т.к. окна не обновляются во время выполнения скрипта) не
        # происходит обновления нодов в композитинге. Решение - показать окно композитинга. Оператор должен работать
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
        partitionsStart = 0
        partitionsEnd = bpy.context.scene.partition_render_vars.xCut * bpy.context.scene.partition_render_vars.yCut
        partitionsCount = bpy.context.scene.partition_render_vars.xCut * bpy.context.scene.partition_render_vars.yCut
        if bpy.context.scene.partition_render_vars.useRange:
            partitionsStart = bpy.context.scene.partition_render_vars.rangeFrom - 1
            partitionsEnd = bpy.context.scene.partition_render_vars.rangeTo
            partitionsCount = bpy.context.scene.partition_render_vars.rangeTo - bpy.context.scene.partition_render_vars.rangeFrom + 1
        for i in range(partitionsStart, partitionsEnd):
            imageName = 'p_' + str(i + 1) + '.' + bpy.context.scene.partition_render_static.tmpFileExtension
            if os.path.exists(self.__class__.dirPath + os.path.sep + imageName):
                bpy.data.images.load(filepath = self.__class__.dirPath + os.path.sep + imageName, check_existing = True)
            # Image
            currentImageNode = group.nodes.new(type = 'CompositorNodeImage')
            currentImageNode.image = bpy.data.images['p_' + str(i + 1) + '.' + bpy.context.scene.partition_render_static.tmpFileExtension]
            locatoinX = i * 200
            locationY = i * -100
            currentImageNode.location = (locatoinX, locationY)
            currentImageNode.name = 'p_' + str(i + 1) + '.' + bpy.context.scene.partition_render_static.tmpFileExtension
            # AlphaOver
            if i > partitionsStart:
                currentAlphaOverNode = group.nodes.new(type = 'CompositorNodeAlphaOver')
                locatoinX = i * 200 + 200
                locationY = (i - 1) * -100
                currentAlphaOverNode.location = (locatoinX, locationY)
                currentAlphaOverNode.name = 'p_' + str(i) + '_' + str(i + 1) + '.' + bpy.context.scene.partition_render_static.tmpFileExtension
                # связи
                # if i == 1:
                if i == (partitionsStart + 1):
                    imageOutputName = self.checkNodeOutputName(group.nodes['p_' + str(i) + '.' + bpy.context.scene.partition_render_static.tmpFileExtension])
                    group.links.new(group.nodes['p_' + str(i) + '.' + bpy.context.scene.partition_render_static.tmpFileExtension].outputs[imageOutputName], currentAlphaOverNode.inputs[1])
                else:
                    group.links.new(group.nodes['p_' + str(i - 1) + '_' + str(i) + '.' + bpy.context.scene.partition_render_static.tmpFileExtension].outputs['Image'], currentAlphaOverNode.inputs[1])
                imageOutputName = self.checkNodeOutputName(group.nodes['p_' + str(i + 1) + '.' + bpy.context.scene.partition_render_static.tmpFileExtension])
                group.links.new(group.nodes['p_' + str(i + 1) + '.' + bpy.context.scene.partition_render_static.tmpFileExtension].outputs[imageOutputName], currentAlphaOverNode.inputs[2])
        # Output
        if partitionsCount == 1:
            imageOutputName = self.checkNodeOutputName(group.nodes['p_' + str(partitionsEnd) + '.' + bpy.context.scene.partition_render_static.tmpFileExtension])
            group.links.new(group.nodes['p_' + str(partitionsEnd) + '.' + bpy.context.scene.partition_render_static.tmpFileExtension].outputs[imageOutputName], groupOutput.inputs['Out'])
        else:
            group.links.new(group.nodes['p_' + str(partitionsEnd - 1) + '_' + str(partitionsEnd) + '.' + bpy.context.scene.partition_render_static.tmpFileExtension].outputs['Image'], groupOutput.inputs['Out'])
        # добавить построенную связку в группу и в композитинг
        nodesField = bpy.context.scene.node_tree
        groupNode = nodesField.nodes.new(type = 'CompositorNodeGroup')
        groupNode.location = (-100, -200)
        groupNode.node_tree = group
        groupNode.name = 'partitionGroup'
        # Composite
        currentComposite = nodesField.nodes.new(type = 'CompositorNodeComposite')
        currentComposite.location = (100, -200)
        currentComposite.name = 'partitionComposite'
        nodesField.links.new(groupNode.outputs['Out'], currentComposite.inputs['Image'])
        # вернуть окно
        if returnAreaAfterCompositingRedraw not in bpy.app.handlers.scene_update_post:
            bpy.app.handlers.scene_update_post.append(returnAreaAfterCompositingRedraw)
        return {'FINISHED'}

    def clearCompositingNodes(self):
        if bpy.context.scene.node_tree:
            for currentNode in bpy.context.scene.node_tree.nodes:
                if currentNode.name == 'partitionGroup' or currentNode.name == 'partitionComposite':
                    bpy.context.scene.node_tree.nodes.remove(currentNode)

    def checkNodeOutputName(self, node):
        outputName = 'Image'
        for currentOutput in node.outputs:
            if currentOutput.name == 'Image':
                break
            if currentOutput.name == 'Combined':
                outputName = 'Combined'
                break
        return outputName

    @classmethod
    def getInfoFileName(cls):
        if not cls.dirPath:
            if bpy.data.filepath:
                cls.dirPath = os.path.dirname(bpy.data.filepath) + os.path.sep + os.path.splitext(os.path.basename(bpy.data.filepath))[0]
            else:
                cls.dirPath = os.path.dirname(bpy.context.user_preferences.filepaths.temporary_directory) + os.path.sep + 'partition_render_unsaved'
        if not os.path.exists(cls.dirPath):
            os.makedirs(cls.dirPath)
        if not cls.infoFile:
            if bpy.data.filepath:
                infoFileName = os.path.splitext(os.path.basename(bpy.data.filepath))[0]+'_pr.json'
            else:
                infoFileName = 'partition_render_unsaved_pr.json'
            cls.infoFile = cls.dirPath + os.path.sep + infoFileName
        return {'FINISHED'}

    def checkFinish(self):
        finish = False
        if bpy.context.scene.partition_render_vars.useRange:
            if self.__class__.currentPartitionNumber > bpy.context.scene.partition_render_vars.rangeTo:
                finish = True
        else:
            if self.__class__.currentPartitionNumber > bpy.context.scene.partition_render_vars.xCut * bpy.context.scene.partition_render_vars.yCut:
                finish = True
        return finish

def returnAreaAfterCompositingRedraw(scene):
    # Возврат окна в предыдущий режим, после показа композитинга для обновления
    bpy.app.handlers.scene_update_post.remove(returnAreaAfterCompositingRedraw)
    bpy.context.window_manager.windows[0].screen.areas[0].type = PartRender.windowToRedrawCompositingType
    return {'FINISHED'}

def onRenderPartitionFinished(scene):
    print('Partition '+str(PartRender.currentPartitionNumber) + ' finished')
    if onRenderPartitionFinished in bpy.app.handlers.render_complete:
        bpy.app.handlers.render_complete.remove(onRenderPartitionFinished)
    if onRenderPartitionCancel in bpy.app.handlers.render_cancel:
        bpy.app.handlers.render_cancel.remove(onRenderPartitionCancel)
    # запустить продолжение обработки
    if afterRenderPartitionFinished not in bpy.app.handlers.scene_update_post:
        bpy.app.handlers.scene_update_post.append(afterRenderPartitionFinished)
    return {'FINISHED'}

def afterRenderPartitionFinished(scene):
    # После успешного завершения рендера очередной партиции
    # на событии обновления сцены, иначе ошибки
    if afterRenderPartitionFinished in bpy.app.handlers.scene_update_post:
        bpy.app.handlers.scene_update_post.remove(afterRenderPartitionFinished)
    # сохранить партицию
    PartRender.savePartitionToFile()
    # рендер следующей партиции
    PartRender.getInfoFileName()
    setNextPartition()
    renderPartition(scene)
    return {'FINISHED'}

def onRenderPartitionCancel(scene):
    if onRenderPartitionFinished in bpy.app.handlers.render_complete:
        bpy.app.handlers.render_complete.remove(onRenderPartitionFinished)
    if onRenderPartitionCancel in bpy.app.handlers.render_cancel:
        bpy.app.handlers.render_cancel.remove(onRenderPartitionCancel)
    PartRender.executing = False
    # Перерисовать окно, иначе обновляет с задержкой
    for area in bpy.context.window_manager.windows[0].screen.areas:
        if area.spaces.active.type == 'PROPERTIES':
            area.tag_redraw()
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
    with open(PartRender.infoFile, 'w') as currentFile:
        json.dump({'currentPartition': PartRender.currentPartitionNumber}, currentFile, indent = 4)
    return {'FINISHED'}

def register():
    bpy.utils.register_class(PartRender)

def unregister():
    bpy.utils.unregister_class(PartRender)
