bl_info = {
    'name': 'Partition Render',
    'category': 'Render',
    'author': 'Nikita Akimov',
    'version': (0, 0, 2),
    'blender': (2, 78, 0),
    'location': 'Properties window > Render tab > Partition Render',
    'wiki_url': 'http://b3d.interplanety.ru/add-on-partition-render/',
    'tracker_url': 'http://b3d.interplanety.ru/add-on-partition-render/',
    'description': 'Allows to split the render into partitions and render them separately'
}

import sys
import importlib

modulesNames = ['RenderBorder', 'PartRender', 'PartRenderPanel']

modulesFullNames = []
for currentModuleName in modulesNames:
    if 'DEBUG_MODE' in sys.argv:
        modulesFullNames.append('{}'.format(currentModuleName))
    else:
        modulesFullNames.append('{}.{}'.format(__name__, currentModuleName))

for currentModuleName in modulesFullNames:
    if currentModuleName in sys.modules:
        importlib.reload(sys.modules[currentModuleName])
    else:
        globals()[currentModuleName] = importlib.import_module(currentModuleName)

def register():
    for currentModuleName in modulesFullNames:
        if currentModuleName in sys.modules:
            if hasattr(sys.modules[currentModuleName], 'register'):
                sys.modules[currentModuleName].register()

def unregister():
    for currentModuleName in modulesFullNames:
        if currentModuleName in sys.modules:
            if hasattr(sys.modules[currentModuleName], 'unregister'):
                sys.modules[currentModuleName].unregister()

if __name__ == "__main__":
    register()
