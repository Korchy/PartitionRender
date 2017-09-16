Partition Render
===============================================================================
Blender add-on: interruptable rendering by number of partitions

Site: <a href="http://b3d.interplanety.ru/add-on-partition-render/">Description</a>

===============================================================================
Installation

User Preferences - Addons - Install from file - select downloaded archive

===============================================================================
Usage

In Properties window - Render Tab - Partition Render subtab

<img src="http://b3d.interplanety.ru/wp-content/upload_content/2017/02/00-400x253.jpg" title="Partition Render">

===============================================================================
Tested with Blender versions:

2.78, 2.79

===============================================================================
Version history:

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
