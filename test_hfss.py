from hfss import get_active_project

project = get_active_project()
design = project.new_em_design("TestDesign")
modeler = design.modeler

# Cavity
bx = design.set_variable("bx", "10mm")
by = design.set_variable("by", "25mm")
bz = design.set_variable("bz", "15mm")
# Tunnel
tx = design.set_variable("tx", "10mm")
ty = design.set_variable("ty", "1mm")
tz = design.set_variable("tz", "1mm")
# Chip
cz = design.set_variable('cz', ".45mm")

def create_cavity(name):
    box = modeler.draw_box_center([0, 0, 0], [bx, by, bz], name=name)
    cyl1 = modeler.draw_cylinder_center([0, by/2, 0], bx/2, bz, axis='Z')
    cyl2 = modeler.draw_cylinder_center([0, -by/2, 0], bx/2, bz, axis='Z')
    modeler.unite([box, cyl1, cyl2])
    return box

cav1 = create_cavity("Cavity1")
cav2 = create_cavity("Cavity2")

modeler.translate(cav1, [(tx+bx)/2, 0, 0])
modeler.translate(cav2, [-(tx+bx)/2, 0, 0])

tunnel = modeler.draw_box_center([0, 0, 0], [tx, ty, tz], name='Tunnel')

cav = modeler.unite([cav1, cav2, tunnel])

chip = modeler.draw_box_corner([-tx/2, -ty/2, -tz/2], [tx, ty, cz], name='Chip', material='sapphire')

cav1.transparency = 1.0
