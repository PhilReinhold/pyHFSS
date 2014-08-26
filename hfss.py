from __future__ import division
from copy import copy

import tempfile
from sympy.parsing import sympy_parser
from win32com.client import Dispatch

class HfssClient(object):
    def __init__(self):
        self.app = Dispatch('AnsoftHfss.HfssScriptInterface')
        self.desktop = self.app.GetAppDesktop()

        self.project = self.desktop.GetActiveProject()
        self.design = self.project.GetActiveDesign()

        self.setup_module = self.design.GetModule("AnalysisSetup")
        self.default_setup_name = self.setup_module.GetSetups()[0] + " : LastAdaptive"
        self.solutions = self.design.GetModule("Solutions")
        self.fields_calc = self.design.GetModule("FieldsReporter")
        self.modeler = self.design.SetActiveEditor("3D Modeler")
        self.output = self.design.GetModule("OutputVariable")


    def n_modes(self):
        fn = tempfile.mktemp()
        self.solutions.ExportEigenmodes(self.default_setup_name, "", fn)
        return len(open(fn, 'r').readlines())


    def set_mode(self, n, phase):
        n_modes = self.n_modes()
        self.solutions.EditSources(
            "TotalFields",
            ["NAME:SourceNames", "EigenMode"],
            ["NAME:Modes", n_modes],
            ["NAME:Magnitudes"] + [ 1 if i+1 == n else 0 for i in range(n_modes)],
            ["NAME:Phases"] + [ phase if i+1 == n else 0 for i in range(n_modes)],
            ["NAME:Terminated"], ["NAME:Impedances"]
        )

    def create_variable(self, name, value):
        # wtf, right?
        self.design.ChangeProperty(
            ["NAME:AllTabs",
             ["NAME:LocalVariableTab",
              ["NAME:PropServers", "LocalVariables"],
              ["Name:NewProps",
               ["NAME:" + name,
                "PropType:=", "VariableProp",
                "UserDef:=", True,
                "Value:=", value]]]])

    def set_variable(self, name, value):
        if name not in self.design.GetVariables():
            self.create_variable(name, value)
        else:
            self.design.SetVariableValue(name, value)

    def get_variable(self, name):
        return self.design.GetVariableValue(name)

    def _attributes_array(self, name=None, nonmodel=False, color=None, transparency=None, material=None):
        arr = ["NAME:Attributes"]
        if name is not None:
            arr.extend(["Name:=", name])
        if nonmodel:
            arr.extend(["Flags:=", "NonModel"])
        if color is not None:
            arr.extend(["Color:=", color])
        if transparency is not None:
            arr.extend(["Transparency:=", transparency])
        if material is not None:
            arr.extend(["MaterialName:=", material])
        return arr

    def _selections_array(self, *names):
        return ["NAME:Selections", "Selections:=", ",".join(names)]

    def draw_box_corner(self, pos, size, **kwargs):
        return self.modeler.CreateBox([
            "NAME:BoxParameters",
            "XPosition:=", pos[0],
            "YPosition:=", pos[1],
            "ZPosition:=", pos[2],
            "XSize:=", size[0],
            "YSize:=", size[1],
            "ZSize:=", size[2],
            ], self._attributes_array(**kwargs))

    def draw_box_center(self, pos, size, **kwargs):
        corner_pos = [simplify_arith_expr("(%s) - (%s)/2" % p) for p in zip(pos, size)]
        return self.draw_box_corner(corner_pos, size, **kwargs)

    def draw_cylinder(self, pos, radius, height, axis, **kwargs):
        assert(axis in "XYZ")
        return self.modeler.CreateCylinder([
            "NAME:CylinderParameters",
            "XCenter:=", pos[0],
            "YCenter:=", pos[1],
            "ZCenter:=", pos[2],
            "Radius:=", radius,
            "Height:=", height,
            "WhichAxis:=", axis,
            "NumSides:=", 0
        ], self._attributes_array(**kwargs))

    def draw_cylinder_center(self, pos, radius, height, axis, **kwargs):
        axis_idx = ["X", "Y", "Z"].index(axis)
        edge_pos = copy(pos)
        edge_pos[axis_idx] = simplify_arith_expr("(%s) - (%s)/2" % (pos[axis_idx], height))
        return self.draw_cylinder(edge_pos, radius, height, axis, **kwargs)

    def unite(self, names, keep_originals=False):
        self.modeler.Unite(
            self._selections_array(*names),
            ["NAME:UniteParameters", "KeepOriginals:=", keep_originals]
        )
        return names[0]

    def intersect(self, names, keep_originals=False):
        self.modeler.Intersect(
            self._selections_array(*names),
            ["NAME:IntersectParameters", "KeepOriginals:=", keep_originals]
        )
        return names[0]

    def translate(self, name, vector):
        self.modeler.Move(
            self._selections_array(name),
            ["NAME:TranslateParameters",
             "TranslateVectorX:=", vector[0],
             "TranslateVectorY:=", vector[1],
             "TranslateVectorZ:=", vector[2] ]
        )

    def set_object_property(self, obj_name, prop_name, value):
        self.modeler.ChangeProperty(
            ["NAME:AllTabs",
             ["NAME:Geometry3DAttributeTab",
              ["NAME:PropServers", obj_name],
              ["Name:ChangedProps",
               ["NAME:" + prop_name,
                "Value:=", value]]]])

    def draw_rect_corner(self, pos, size):
        pass


def simplify_arith_expr(expr):
    return repr(sympy_parser.parse_expr(str(expr)))

client = HfssClient()

class HfssObject(object):
    def __init__(self, name):
        self.name = name

    def get_bounding_box(self):
        return client.modeler.GetModel



class CalcObject(object):
    client = client
    def __init__(self, stack):
        self.stack = stack
        self.calc_module = self.client.fields_calc

    def _bin_op(self, other, op):
        if isinstance(other, (int, float)):
            other = ConstantCalcObject(other)

        stack = self.stack + other.stack
        stack.append(("CalcOp", op))
        return CalcObject(stack)

    def _unary_op(self, op):
        stack = self.stack[:]
        stack.append(("CalcOp", op))
        return CalcObject(stack)

    def __add__(self, other):
        return self._bin_op(other, "+")

    def __radd__(self, other):
        return self + other

    def __sub__(self, other):
        return self._bin_op(other, "-")

    def __rsub__(self, other):
        return (-self) + other

    def __mul__(self, other):
        return self._bin_op(other, "*")

    def __rmul__(self, other):
        return self * other

    def __div__(self, other):
        return self._bin_op(other, "/")

    def __rdiv__(self, other):
        other = ConstantCalcObject(other)
        return other / self

    def __pow__(self, other):
        return self._bin_op(other, "Pow")

    def __neg__(self):
        return self._unary_op("Neg")

    def __abs__(self):
        return self._unary_op("Abs")

    def scalar_x(self):
        return self._unary_op("ScalarX")

    def scalar_y(self):
        return self._unary_op("ScalarY")

    def scalar_z(self):
        return self._unary_op("ScalarZ")

    def real(self):
        return self._unary_op("Real")

    def imag(self):
        return self._unary_op("Imag")

    def _integrate(self, name, type):
        stack = self.stack + [(type, name), ("CalcOp", "Integrate")]
        return CalcObject(stack)

    def integrate_line(self, name):
        return self._integrate(name, "EnterLine")

    def integrate_surf(self, name="AllObjects"):
        return self._integrate(name, "EnterSurf")

    def integrate_vol(self, name="AllObjects"):
        return self._integrate(name, "EnterVol")

    def write_stack(self):
        for fn, arg in self.stack:
            getattr(self.calc_module, fn)(arg)

    def save_as(self, name):
        self.write_stack()
        self.calc_module.AddNamedExpr(name)
        return NamedCalcObject(name)

    def evaluate(self, n_mode=1, phase=0):
        self.write_stack()
        self.client.set_mode(n_mode, 0)
        setup_name = self.client.default_setup_name
        vars = ["Phase:=", str(int(phase))+"deg"]
        self.calc_module.ClcEval(setup_name, vars)
        return float(self.calc_module.GetTopEntryValue(setup_name, vars)[0])


class NamedCalcObject(CalcObject):
    def __init__(self, name):
        stack = [("CopyNamedExprToStack", name)]
        super(NamedCalcObject, self).__init__(stack)

class ConstantCalcObject(CalcObject):
    def __init__(self, num):
        stack = [("EnterScalar", num)]
        super(ConstantCalcObject, self).__init__(stack)


Mag_E = NamedCalcObject("Mag_E")
Mag_H = NamedCalcObject("Mag_H")
Mag_Jsurf = NamedCalcObject("Mag_Jsurf")
Mag_Jvol = NamedCalcObject("Mag_Jvol")
Vector_E = NamedCalcObject("Vector_E")
Vector_H = NamedCalcObject("Vector_H")
Vector_Jsurf = NamedCalcObject("Vector_Jsurf")
Vector_Jvol = NamedCalcObject("Vector_Jvol")
ComplexMag_E = NamedCalcObject("ComplexMag_E")
ComplexMag_H = NamedCalcObject("ComplexMag_H")
ComplexMag_Jsurf = NamedCalcObject("ComplexMag_Jsurf")
ComplexMag_Jvol = NamedCalcObject("ComplexMag_Jvol")
