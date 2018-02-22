#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
VHDL Classes
============

.. moduleauthor:: Jordi Masip <jordi@masip.cat>
"""

class VHDL(object):

    def __init__(self):
        self._libs = []
        self._entities = {}
        self._archs = {}

    def setEntity(self, ent):
        if isinstance(ent, Entity):
            self._entities[ent.getName()] = ent

    def getEntities(self):
        return self._entities.values()

    def getEntityByName(self, ent_name):
        if ent_name in self._entities.keys():
            return self._entities[ent_name]
        return False

    def setArchitecture(self, arch):
        if isinstance(arch, Architecture):
            self._archs[arch.getName()] = arch

    def getArchitectures(self):
        return self._archs.values()

    def getArchitectureByName(self, arch_name):
        if arch_name in self._arch.keys():
            return self._arch[arch_name]
        return False

    def addLibrary(self, lib):
        if isinstance(lib, Library):
            if lib not in self._libs:
                self._libs += [lib]
                return True
        return False

    def removeLibrary(self, lib):
        try:
            self._libs.remove(lib)
            return True
        except Exception:
            return False

    def getLibs(self):
        """
        Returns a list of Libraries
        """
        return self._libs

    def __str__(self):
        return "\n".join([str(l) for l in self._libs])

class Library(object):

    def __init__(self, value):
        self._lib = value
        self._packages = []

    def addPackage(self, package_name):
        if self._lib + "." + package_name not in self._packages:
            self._packages += [self._lib + "." + package_name]
        else:
            print("error: the package '{0}' is already in the library".format(package_name))

    def getPackages(self):
        return self._packages

    def getName(self):
        return self._lib

    def __eq__(self, other):
        if isinstance(other, Library):
            return self._lib == other.getName()
        return False

    def __str__(self):
        return "<Library %s>" % self._lib

class Entity(object):

    def __init__(self, name):
        self._name = name
        self._port = {}
        self._generic = {}
        self.rst = ""
        self.rstActiveLow = True
        self.clk = ""

    def getName(self):
        return self._name

    def setPortList(self, p):
        if isinstance(p, PortList):
            self._port = p.getPorts()
            return True
        return False

    def getPorts(self):
        return self._port

    def setGenericList(self, p):
        if isinstance(p, GenericList):
            self._generic = p.getGenerics()
            return True
        return False

    def getGenerics(self):
        return self._generic

    def __str__(self):
        return "<Entity %s>" % self._name

    def __eq__(self, other):
        return self._name == other.getName() if isinstance(other, Entity) else False

class Signal(object):

    _obj_name = "signal"
    _name = ""
    _type = ""
    _value = ""

    def __init__(self, name, t, value=""):
        self.setName(name)
        self.setType(t)
        self.setValue(value)

    def getName(self):
        return self._name

    def setName(self, n):
        if isinstance(n, str):
            self._name = n
        else:
            print("error: the name '%s' must be a string" % self._obj_name)

    def setValue(self, val):
        self._value = val

    def getValue(self):
        return self._value

    def getType(self):
        return self._type

    def setType(self, t):
        if isinstance(t, str):
            self._type = t
        else:
            print("error: the type '%s' must be a string" % self._obj_name)

    def __str__(self):
        if self._value == "":
            return "<%s %s : %s>" % (self._obj_name.capitalize(), self._name, self._type)
        else:
            return "<%s %s : %s := %s>" % (self._obj_name.capitalize(), self._name, self._type, self._value)

    def __eq__(self, other):
        if isinstance(other, Signal):
            return self._name == other.getName() and self._type == other.getType()
        return False

class SignalList(object):

    def __init__(self, signal_str):
        self._signals = self._getSignalFromString(signal_str.strip())

    def getSignals(self):
        return self._signals

    def _getSignalFromString(self, s):
        signals = {}
        try:
            for signal in s.split(";"):
                signal = signal.strip()
                if signal == "":
                    break
                isSignalWithAssignation = ":=" in signal
                if isSignalWithAssignation:
                    left, assignation = signal.split(":=")
                else:
                    left = signal
                if ":" not in left:
                    print("warning: line '%s' was ignored" % left.strip())
                    continue
                port_prefix, t = left.strip().split(":")
                port_prefix = port_prefix.strip()
                for i in range(len(port_prefix)):
                    if port_prefix[i] == " ":
                        variable_type = port_prefix[:i].strip()
                        port_prefix = port_prefix[i+1:].strip()
                        break
                else:
                    print("error: the signal '%s' is invalid" % signal)
                    return signals
                if variable_type == "type":
                    continue
                t = t.strip()
                if "," in port_prefix:
                    for n in port_prefix.split(","):
                        n = n.strip()
                        signal = Signal(n, t)
                        if isSignalWithAssignation:
                            signal.setValue(assignation)
                        signals[n] = signal
                else:
                    signal = Signal(port_prefix, t)
                    if isSignalWithAssignation:
                        signal.setValue(assignation)
                    signals[port_prefix] = signal
        except Exception as e:
            print("error: cannot read 'signal': %s" % e)
        return signals

class Generic(Signal):

    _obj_name = "generic"

    def __init__(self, name, t, value):
        Signal.__init__(self, name, t, value)

    def __eq__(self, other):
        if isinstance(other, Generic):
            return self._name == other.getName() and self._type == other.getType()
        return False

class Port(Signal):

    _obj_name = "port"
    _port_type = "in"

    def __init__(self, name, port_type, t):
        Signal.__init__(self, name, t)
        self.setPortType(port_type)

    def setPortType(self, t):
        if t in ["in", "out", "inout", "buffer", "linkage"]:
            self._port_type = t
        else:
            print("error: '%s' is an invalid port type for %s '%s'" % (str(t), self._obj_name, self._name))

    def getPortType(self):
        return self._port_type

    def __str__(self):
        return "<%s %s : %s %s>" % (self._obj_name.capitalize(), self._name, self._port_type, self._type)

    def __eq__(self, other):
        if isinstance(other, Port):
            return self._name == other.getName() and self._type == other.getType() and self._port_type == other.getPortType()
        return False

class PortList(object):

    def __init__(self, port_str):
        self._ports = self._getPortFromString(port_str.strip())
        if self._ports == None:
            self._ports = {}

    def getPorts(self):
        return self._ports

    def _getPortFromString(self, s):
        ports = {}
        counting = False
        skip_times, bracket_count = 0, 0
        between_port = ""
        for i in range(len(s)):
            if skip_times > 0:
                skip_times -= 1
                continue
            elif s[i:i+4] == "port":
                counting = True
                skip_times = 3
                continue
            elif s[i] == "(":
                bracket_count += 1
            elif s[i] == ")":
                bracket_count -= 1
                if bracket_count == 0:
                    break
            if counting:
                between_port += s[i]
        port = between_port.strip()[1:].replace("\n", "")
        for p in port.split(";"):
            port_name, t = p.split(":")
            port_name = port_name.strip()
            if port_name[0:2] == "--":
                continue
            t = t.strip()
            for i in range(len(t)):
                if t[i] == " ":
                    port_type = t[:i].strip()
                    variable_type = t[i+1:].strip()
                    break
            if "," in port_name:
                for n in port_name.split(","):
                    n = n.strip()
                    ports[n] = Port(n, port_type, variable_type)
            else:		
                ports[port_name] = Port(port_name, port_type, variable_type)
        return ports

class GenericList(object):

    def __init__(self, generic_str):
        self._generics = self._getGenericFromString(generic_str.strip())
        if self._generics == None:
            self._generics = {}

    def getGenerics(self):
        return self._generics

    def _getGenericFromString(self, s):
        generics = {}
        counting = False
        skip_times, bracket_count = 0, 0
        between_generic = ""
        for i in range(len(s)):
            if skip_times > 0:
                skip_times -= 1
                continue
            elif s[i:i+7] == "generic":
                counting = True
                skip_times = 6
                continue
            elif s[i] == "(":
                bracket_count += 1
            elif s[i] == ")":
                bracket_count -= 1
                if bracket_count == 0:
                    break
            if counting:
                between_generic += s[i]
        try:
            generic = between_generic.strip()[1:].replace("\n", "")
            for p in generic.split(";"):
                isGenericWithAssignment = ":=" in p
                if isGenericWithAssignment:
                    left, assignment = p.split(":=")
                else:
                    left = generic
                generic_name, t = left.split(":")
                generic_name = generic_name.strip()
                if generic_name[0:2] == "--":
                    continue
                t = t.strip()
                assignment = assignment.strip()
                if "," in generic_name:
                    for n in generic_name.split(","):
                        n = n.strip()
                        generics[n] = Generic(n, t, assignment)
                else:
                    generics[generic_name] = Generic(generic_name, t, assignment)
        except Exception as e:
            print("error: the generic is malformed")
        return generics

class Architecture(object):

    _begin = ""
    _name = ""
    _archOf = None

    def __init__(self, name, ent):
        if isinstance(name, str):
            self._name = name
        else:
            print("error: the arch '%s' must be a string" % name)
        if isinstance(ent, Entity):
            self._archOf = ent
        else:
            print("error: architecture '%s' has an invalid entity" % self._name)

    def getName(self):
        return self._name

    def getEntity(self):
        return self._archOf

    def setSignalList(self, sl):
        if isinstance(sl, SignalList):
            self._signals = sl.getSignals()
            return True
        return False

    def getSignalList(self):
        return self._signals

    def getEntity(self):
        return self._archOf

    def __str__(self):
        return "<Architecture %s of %s>" % (self._name, self._archOf.getName())
