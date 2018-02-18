#!/usr/bin/python2
# -*- coding: utf-8 -*-

import sys
from vhdl import *
from vParser import *

def libraryTb():
    libs, uses = [], []
    for l in vhdl.getLibs():
        libs += ['library %s;' % l.getName()]
        uses += ['use %s;' % p for p in l.getPackages()]
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
        result += 'architecture behav of %s_tb is\n\tcomponent %s\n' % (entity.getName(), entity.getName())
        result += generics[1] + portsTb() + generics[0] + clk[0] + dutSignalsTb() + dutTb() + clk[1] + resetTb()
        result += '\n\t-- Add stimulus process here:\nend behav;' # TODO Add assert false at end
    return result

def genericsTb():
    result = '\tgeneric ('
    constants = ""
    for arch in vhdl.getArchitectures():
        ent = arch.getEntity()
        generics = ['\t{0} : {1};\n'.format(g.getName(), g.getType()) for g in ent.getGenerics().values()]
        result += "\t\t".join(generics)[:-2] + ');\n'
        for g in ent.getGenerics().values():
            constants += '\tconstant {0} : {1} := {2};\n'.format(g.getName(), g.getType(), g.getValue())
    return (constants, result)

def portsTb():
    result = '\tport ('
    for arch in vhdl.getArchitectures():
        ent = arch.getEntity()
        ports = ['\t{0} : {1} {2};\n'.format(p.getName(), p.getPortType(), p.getType()) for p in ent.getPorts().values()]
        result += "\t\t".join(ports)[:-2] + ');\n\tend component;\n\n'
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
        result += "port map (\n"
        for p in entity.getPorts().values():
            result += '\t\t%s => %s,\n' % (p.getName(), p.getName())
        result = result[:-2] + ");\n"
    return result

def resetTb():
    rst = False
    activeHigh = True
    for x in list(vhdl.getEntities())[0].getPorts():
        if x.find("rst") >= 0 or x.find("reset") >= 0:
            rst = True
            if x.find("n") >= 0:
                activeHigh = False
    if rst:
        while True:
            try:
                rst_len = input("Number of periods to hold rst (default 5): ") # TODO: make sure reset is deasserted on the falling edge
                if rst_len == "":
                    rst_len = "5"
                rst_len = float(rst_len)
                if rst_len > 0:
                    break
            except Exception as e:
                print(e)
                print("error: Invalid reset length")

        return "\n\n\trst_process: process\n\tbegin\n\t\trst <= '%d';\n\t\twait for %d*clk_period;\n\t\trst <= '%d';\n\t\twait;\n\tend process rst_process;" % (activeHigh, rst_len, not activeHigh)
    else:
        return ""

def clockTb():
    clk = False
    for x in list(vhdl.getEntities())[0].getPorts():
        if x == 'clk' or x == 'clock' or x == 'i_clk' or x == 'i_clock':
            clk = True
    if clk:
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

        return ("\tconstant clk_period : time := {0} ns;\n".format(clk_freq), "\n\n\tclk_process: process\n\tbegin\n\t\tclk <= '0';\n\t\twait for clk_period/2;\n\t\tclk <= '1';\n\t\twait for clk_period/2;\n\tend process clk_process;")
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
    [vhdl.addLibrary(l) for l in parseLibs(vhd_file)] # TODO add numeric_std if not present
    [vhdl.setEntity(e) for e in parseEntities(vhd_file)]

    # Get each entity in 'vhdl' and adds each architecture in 'vhdl'
    for entity in vhdl.getEntities():
        arch = parseArchitectureOfEntity(vhd_file, entity)
        if arch != "":
            vhdl.setArchitecture(arch)

    # Write to file
    write_file(vhdl_filename, libraryTb() + entityTb() + architectureTb())
    print("\nThe file '%s' was created successfully." % vhdl_filename)
