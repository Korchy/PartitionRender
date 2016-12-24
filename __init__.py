bl_info = {
    'name': 'Partition Render',
    'category': 'Render',
    'author': 'Nikita Akimov',
    'version': (0, 0, 3),
    'blender': (2, 78, 0),
    'location': 'Properties window > Render tab > Partition Render',
    'wiki_url': 'http://b3d.interplanety.ru/add-on-partition-render/',
    'tracker_url': 'http://b3d.interplanety.ru/add-on-partition-render/',
    'description': 'Allows to split the render into partitions and render them separately'
}

import sys
import importlib

modulesNames = ['RenderBorder', 'PartRender', 'PartRenderPanel']

modulesFullNames = {}
for currentModuleName in modulesNames:
    if 'DEBUG_MODE' in sys.argv:
        modulesFullNames[currentModuleName] = ('{}'.format(currentModuleName))
    else:
        modulesFullNames[currentModuleName] = ('{}.{}'.format(__name__, currentModuleName))

for currentModuleFullName in modulesFullNames.values():
    if currentModuleFullName in sys.modules:
        importlib.reload(sys.modules[currentModuleFullName])
    else:
        globals()[currentModuleFullName] = importlib.import_module(currentModuleFullName)
        setattr(globals()[currentModuleFullName], 'modulesNames', modulesFullNames)

def register():
    for currentModuleName in modulesFullNames.values():
        if currentModuleName in sys.modules:
            if hasattr(sys.modules[currentModuleName], 'register'):
                sys.modules[currentModuleName].register()

def unregister():
    for currentModuleName in modulesFullNames.values():
        if currentModuleName in sys.modules:
            if hasattr(sys.modules[currentModuleName], 'unregister'):
                sys.modules[currentModuleName].unregister()

if __name__ == "__main__":
    register()
