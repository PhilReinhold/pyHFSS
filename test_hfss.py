from hfss import client

# Cavity
client.set_variable("bx", "10mm")
client.set_variable("by", "25mm")
client.set_variable("bz", "15mm")
# Tunnel
client.set_variable("tx", "10mm")
client.set_variable("ty", "1mm")
client.set_variable("tz", "1mm")
# Chip
client.set_variable('cz', ".45mm")

def create_cavity(name):
    box = client.draw_box_center([0, 0, 0], ["bx", "by", "bz"], name=name)
    cyl1 = client.draw_cylinder_center([0, "by/2", 0], "bx/2", "bz", axis='Z')
    cyl2 = client.draw_cylinder_center([0, "-by/2", 0], "bx/2", "bz", axis='Z')
    client.unite([box, cyl1, cyl2])
    return box

cav1 = create_cavity("Cavity1")
cav2 = create_cavity("Cavity2")

client.translate(cav1, ["(tx+bx)/2", 0, 0])
client.translate(cav2, ["-(tx+bx)/2", 0, 0])

tunnel = client.draw_box_center([0, 0, 0], ["tx", "ty", "tz"], name='Tunnel')

cav = client.unite([cav1, cav2, tunnel])

chip = client.draw_box_corner(["-tx/2", "-ty/2", "-tz/2"], ["tx", "ty", "cz"], name='Chip', material='sapphire')

client.set_object_property(cav, 'Transparent', 0.9)
