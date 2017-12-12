# PlazaRoute QGIS-Plugin

This is the QGIS Plugin, which acts as a frontend to the [PlazaRoute service](https://github.com/PlazaRoute/plazaroute/tree/master/plaza_routing)

## Requirements
* QGIS 2.18
* A running instance of the [PlazaRoute Backend](https://github.com/PlazaRoute/plazaroute/tree/master/plaza_routing)
* This plugin was tested under Fedora 26 and Ubuntu 16.04

## Installation
* The path to the backend API can be configured in [config.py](https://github.com/PlazaRoute/qgis/blob/master/config.py)
* Clone the Repository into `PlazaRoute`:

```
git clone https://github.com/PlazaRoute/qgis.git PlazaRoute
```

* Copy the entire `PlazaRoute` folder to the QGIS Plugin directory
    * `~/.qgis2/python/plugins/` on Linux
    * `%userprofile%/.qgis2/python/plugins/` on Windows
* Start QGIS
* *Plugins -> Manage and Install Plugins...*
* Under *Installed*, activate the checkbox for `PlazaRoute`
* The Plugin can be found under *Plugins -> PlazaRoute*
