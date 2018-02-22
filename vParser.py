#!/usr/bin/python3
# -*- coding: utf-8 -*-

from vhdl import *
import sys, os

"""
vParser
=======

.. moduleauthor:: Jordi Masip <jordi@masip.cat>
"""

def read_file(filename):
    if not os.path.isfile(filename):
        print("error: file '%s' does not exist" % filename)
        sys.exit(1)

    try:
        with open(filename, "r") as f:
            content = f.read()
            return content

    except Exception as e:
        print("error: failed to open file '%s'" % filename)
        sys.exit(1)

def write_file(filename, content):
    with open(filename, "w") as f:
        f.write(content)

def getBetween(s, pref, suf):
    try:
        start = 0 if pref == "" else s.index(pref)
        end = len(s) if suf == "" else s[start:].index(suf)
        return (s[start + len(pref):start+end], start+end)
    except Exception:
        return ("", -1)

def parseLibs(vhdl_file):
    libs = {}
    if "library" not in vhdl_file:
        return []

    last_pos = 0

    while True:
        value = getBetween(vhdl_file[last_pos:], "library", ";")

        ignore_line = False

        for i in range(last_pos, last_pos + len(value[0]))[::-1]:
            if vhdl_file[i] == '\n':
                break

            if vhdl_file[i] == '-' and vhdl_file[i-1] == '-':
                ignore_line = True
                break

        last_pos += value[1]

        if value == ("", -1):
            break

        lib_name = value[0].strip().lower()

        if lib_name in libs:
            break

        if not ignore_line:
            libs[lib_name] = Library(lib_name)
    last_pos = 0

    libs["work"] = Library("work") # Present by default

    while True:
        value = getBetween(vhdl_file[last_pos:], "use", ";")

        ignore_line = False

        for i in range(last_pos, last_pos + len(value[0]))[::-1]:
            if vhdl_file[i] == '\n':
                break

            if vhdl_file[i] == '-' and vhdl_file[i-1] == '-':
                ignore_line = True
                break

        last_pos += value[1]

        if value == ("", -1):
            break

        use_statment = value[0].strip().lower().split(".")
        lib, package = use_statment[0], ".".join(use_statment[1:])

        if not ignore_line:
            if lib in libs.keys():
                libs[lib].addPackage(package)
            else:
                print("error: library '%s' is being used by the package '%s.%s' but has not been added" % (lib, lib, package))
            break

    return libs.values()

def parsePortsGenerics(vhdl_file, entity, isPort):
    port = ""
    search_string = ""
    if isPort:
        search_string = "port"
    else:
        search_string = "generic"
    bracket_counter = 0
    isCounting, isPortFound, isValidPort = False, False, False
    between_entity = getBetween(vhdl_file, entity.getName() + " is", "end")[0].strip()

    for i in range(len(between_entity)):
        if between_entity[i:i+len(search_string)] == search_string:
            isCounting = True
            isPortFound = True
        if isCounting:
            port += between_entity[i]
            if between_entity[i] == "(":
                bracket_counter += 1
            elif between_entity[i] == ")":
                bracket_counter -= 1
            elif between_entity[i] == ";" and bracket_counter == 0:
                isPortFound = True
                isValidPort = True
                break
    else:
        isValidPort = False

    if isValidPort:
        if isPort:
            entity.setPortList(PortList(port))
            ports = set(entity.getPorts().keys())
            clks = ['clk', 'clock']
            rsts = ['rst', 'reset']
            clk_search = True
            for search_port in [clks, rsts]:
                port = [port for port in ports if any(x in port for x in search_port)]
                if port:
                    port = port[0] # TODO Deal with multiple clocks/resets
                if clk_search:
                    entity.clk = port
                    clk_search = False # TODO This is probably not the best way
                else:
                    entity.rst = port
                    if port.find("n") >= 0:
                        entity.rstActiveLow = True
                    else:
                        entity.rstActiveLow = False
        else:
            entity.setGenericList(GenericList(port))
    elif isPortFound:
        print("error: illegal or missing port/generic definition")

def parseEntities(vhdl_file):
    entities = []
    last_pos = 0

    while True:
        value = getBetween(vhdl_file[last_pos:], "entity", "is")
        entity = Entity(value[0].strip())

        if value == ("", -1) or entity in entities:
            break

        last_pos += value[1]
        parsePortsGenerics(vhdl_file, entity, False) # get generics
        parsePortsGenerics(vhdl_file, entity, True) # get ports

        entities += [entity]

    return entities

def parseArchitectureOfEntity(vhdl_file, entity):
    last_pos = 0

    while True:
        value = getBetween(vhdl_file[last_pos:], "architecture", "begin")
        last_pos += value[1]
        arch_name = getBetween(value[0], "", " of")[0].strip()
        ent_name = getBetween(value[0], "of ", "is")[0].strip()

        if arch_name == "" or ent_name == "":
            break
        if ent_name != entity.getName():
            continue

        arch = Architecture(arch_name, entity)
        signals = getBetween(value[0], "is", "")[0].strip()

        if signals != "":
            arch.setSignalList(SignalList(signals))

        return arch

    print("error: no architectures found for '%s'" % entity.getName())
    sys.exit(1)
