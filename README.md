pyHFSS
======

HFSS scripting interface in python

Create a Design
---------------

```python
from hfss import get_active_project
proj = get_active_project()
design = proj.insert_dm_design("Test")
```
    
Or Get an Existing Design
-------------------------

```python
from hfss import get_active_design
design = get_active_design()
```

Creating Variables
------------------

```python
bx = design.set_variable("Box_X", "3mm")
by = design.set_variable("Box_Y", "6mm")
bz = design.set_variable("Box_Z", "1mm")
```
    

3D Modeler
----------

```python
modeler = design.modeler
modeler.draw_box_center([0,0,0], [bx, by, bz], material="silicon")
```

Setup Analysis
--------------

```python
setup = design.create_dm_setup(freq_ghz=5)
sweep = setup.insert_sweep(4, 10, count=1000)
setup.analyze()
freqs, (S12, Y11) = sweep.get_network_data("S12,Y11")
```

Fields Calculator
-----------------

```python
fields = setup.get_fields()
Mag_E_Sq = fields.Mag_E ** 2
Surface_E = Mag_E_Sq.integrate_surf("Object Name")
print Surface_E.evaluate()
```


Keyword Arguments for Drawing Commands
--------------------------------------

  - name: str
  - nonmodel: bool
  - color: (int, int, int) each in [0...255]
  - transparency: float in [0, 1]
  - material: str (matching existing material name)

HFSS refuses to close
---------------------

If your script terminates improperly, this can happen. pyHFSS tries to
catch termination events and handle them. Your safety should be
guaranteed however, if you call `hfss.release()` when you have finished
