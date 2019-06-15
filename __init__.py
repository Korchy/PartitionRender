# Nikita Akimov
# interplanety@interplanety.org

from .addon import Addon
import sys
import importlib

bl_info = {
    'name': 'Partition Render',
    'category': 'Render',
    'author': 'Nikita Akimov',
    'version': (0, 0, 5),
    'blender': (2, 79, 0),
    'location': 'Properties window > Render tab > Partition Render',
    'wiki_url': 'https://b3d.interplanety.org/en/partitionrender-add-on/',
    'tracker_url': 'https://b3d.interplanety.org/en/partitionrender-add-on/',
    'description': 'Allows to split the render into partitions and render them separately'
}

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
    if not Addon.dev_mode():
        for currentModuleName in modulesFullNames.values():
            if currentModuleName in sys.modules:
                if hasattr(sys.modules[currentModuleName], 'register'):
                    sys.modules[currentModuleName].register()
    else:
        print('It seems you are trying to use the dev version of the ' + bl_info['name'] + ' add-on. It may work not properly. Please download and use the release version!')


def unregister():
    if not Addon.dev_mode():
        for currentModuleName in modulesFullNames.values():
            if currentModuleName in sys.modules:
                if hasattr(sys.modules[currentModuleName], 'unregister'):
                    sys.modules[currentModuleName].unregister()


if __name__ == "__main__":
    register()
