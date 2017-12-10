# Partition Render

Blender add-on: interruptable rendering by number of partitions

Author: Nikita Akimov interplanety@interplanety.org

<a href="https://b3d.interplanety.org/en/partitionrender-add-on/">Add-on web site</a>


**Installation**

User Preferences - Addons - Install Add-on from File - select downloaded archive

**Usage**

Location: Properties window - Render Tab - Partition Render subtab

<img src="https://b3d.interplanety.org/wp-content/upload_content/2017/12/01-400x208.jpg" title="Partition Render">

**Tested with Blender versions:**

2.78, 2.79

**Version history:**

0.0.1
- This release

0.0.2
- Range selection added
- Fixed an error with unsaved blender projects

0.0.3
- Added "Reset" and "Clear" buttons
- Checking "Use Range" checkbox resets partition to the first

0.0.4
- Compositing nodes for final image combining connected to a separate output Compositing node and removed each time partition render starts.

0.0.5
- Added "SaveMultilayer" checkbox. If the checkbox is on - temporary render results saved in OpenEXR Multilayer format including all layers and passes for future use. Only finished image compiles automatically, different passes need to compile manually.
