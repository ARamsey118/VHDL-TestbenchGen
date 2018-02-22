#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from vhdl import *
from vParser import *

def libraryTb():
    libs, uses = [], []
    for l in vhdl.getLibs():
        uses += ['use %s;' % p for p in l.getPackages()]
        if l.getName() == "work":
            continue # skip work library, but not work packages
        libs += ['library %s;\n' % l.getName()]
    numeric_std = 'use ieee.numeric_std.all;'
    if numeric_std not in uses and 'library ieee;\n' in libs:
        uses += [numeric_std] 
    return "%s%s\n\n" % ("\n".join(libs), "\n".join(uses))

def entityTb():
    entities = ['entity tb_%s is\nend tb_%s;' % (a.getEntity().getName(), a.getEntity().getName()) for a in vhdl.getArchitectures()]
    return "\n".join(entities) + "\n\n"

def architectureTb():
    result = ""
    for architecture in vhdl.getArchitectures():
        entity = architecture.getEntity()
        clk = clockTb()
        generics = genericsTb()
        result += 'architecture behav of tb_%s is\n\tcomponent %s\n' % (entity.getName(), entity.getName())
        result += generics[1] + portsTb() + generics[0] + clk[0] + dutSignalsTb() + dutTb() + clk[1] + resetTb()
        result += "\n\n\tstim_process: process\nbegin\n\t\t"
        if entity.rst:
            result += "wait until {0} = '{1}';\n\t\t".format(entity.rst, int(entity.rstActiveLow))
        result += "--insert stimulus here\n\n\t\tassert false\n\t\t\treport \"Simulation finished\"\n\t\t\tseverity failure;\n\tend process stim_process;\n\nend behav;"
    return result

def genericsTb():
    result = '\tgeneric (\n\t\t'
    constants = ""
    for arch in vhdl.getArchitectures():
        ent = arch.getEntity()
        generics = ['\t{0} : {1};\n'.format(g.getName(), g.getType()) for g in ent.getGenerics().values()]
        result += "\t\t".join(generics)[:-2] + '\n\t);\n'
        if generics == []:
            result = ""
        for g in ent.getGenerics().values():
            constants += '\tconstant {0} : {1} := {2};\n'.format(g.getName(), g.getType(), g.getValue())
    return (constants, result)

def portsTb():
    result = '\tport (\n\t\t'
    for arch in vhdl.getArchitectures():
        ent = arch.getEntity()
        ports = ['\t{0} : {1} {2};\n'.format(p.getName(), p.getPortType(), p.getType()) for p in ent.getPorts().values()]
        result += "\t\t".join(ports)[:-2] + '\n\t);\n\tend component;\n\n'
    return result

def dutSignalsTb():
    result = ""
    for arch in vhdl.getArchitectures():
        e = arch.getEntity()
        result += "\n".join(['\tsignal %s : %s;' % (p.getName(), p.getType()) for p in e.getPorts().values()])
        result += '\n\n\tbegin\n'
    return result

def dutTb():
    result = ""
    for architecture in vhdl.getArchitectures():
        entity = architecture.getEntity()
        result += '\tUUT: %s ' % entity.getName()
        g = entity.getGenerics().values()
        if g:
            result += "generic map (\n"
            for generic in g:
                result += '\t\t%s => %s,\n' % (generic.getName(), generic.getName())
            result = result[:-2] + "\n\t)\n"
        result += "\tport map (\n"
        for p in entity.getPorts().values():
            result += '\t\t%s => %s,\n' % (p.getName(), p.getName())
        result = result[:-2] + "\n\t);\n"
    return result

def resetTb():
    clk = True
    clkStr = "*clk_period"
    rst_len = 0
    entity = list(vhdl.getEntities())[0]
    rst = entity.rst
    if not entity.clk:
        confirm = input("No clock is present, but reset is. Add reset anyway? [Y/n] ")
        if "n" in confirm.lower():
            rst = ""
        else:
            clkStr = "100 ns"
            clk = False
    if rst:
        while True and clk:
            try:
                rst_len = input("Number of periods to hold rst (default 5): ") 
                if rst_len == "":
                    rst_len = "5"
                rst_len = int(rst_len) # rising clk edges happen at half periods, so this forces falling edge deassertion
                if rst_len > 0:
                    break
            except Exception as e:
                print(e)
                print("error: Invalid reset length")

        return "\n\n\trst_process: process\n\tbegin\n\t\t%s <= '%d';\n\t\twait for %s%s;\n\t\t%s <= '%d';\n\t\twait;\n\tend process rst_process;" % (rst, not entity.rstActiveLow, rst_len if clk else "", clkStr, rst, entity.rstActiveLow)
    else:
        return ""

def clockTb():
    clk = False
    if list(vhdl.getEntities())[0].clk:
        while True:
            try:
                clk_freq = input("Enter clock period (ns) (default 10): ")
                if clk_freq == "":
                    clk_freq = "10"
                clk_freq = int(clk_freq)
                if clk_freq > 0:
                    break
            except Exception as e:
                print(e)
                print("error: Invalid frequency")

        return ("\tconstant clk_period : time := {0} ns;\n".format(clk_freq), "\n\n\tclk_process: process\n\tbegin\n\t\t{0} <= '0';\n\t\twait for clk_period/2;\n\t\t{0} <= '1';\n\t\twait for clk_period/2;\n\tend process clk_process;".format(list(vhdl.getEntities())[0].clk)) 
    else:
        return ("", "")

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("usage: {} <VHDL file>.vhd".format(sys.argv[0]))
        sys.exit(1)

    vhdl_filename = sys.argv[1].split('.')

    if vhdl_filename[-1] != 'vhd':
        print('error: file must have a vhd extenstion')
        sys.exit(1)

    vhdl_filename = vhdl_filename[0].split('/')
    vhdl_filename[-1] = 'tb_' + vhdl_filename[-1]
    # VHDL_tb filename
    vhdl_filename = "/".join(vhdl_filename) + '.vhd'

    # VHDL content
    vhd_file = read_file(sys.argv[1])

    # Creating VHDL obj
    vhdl = VHDL()
    libs = parseLibs(vhd_file)
    [vhdl.addLibrary(l) for l in libs]
    [vhdl.setEntity(e) for e in parseEntities(vhd_file)]

    # Get each entity in 'vhdl' and adds each architecture in 'vhdl'
    for entity in vhdl.getEntities():
        arch = parseArchitectureOfEntity(vhd_file, entity)
        if arch != "":
            vhdl.setArchitecture(arch)

    # Write to file
    write_file(vhdl_filename, libraryTb() + entityTb() + architectureTb())
    print("\nThe file '%s' was created successfully." % vhdl_filename)
