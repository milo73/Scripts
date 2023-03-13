import json
import os
import re
import sys

#
# Copyright
#
copyright = [
    "BEGIN OF TEST\n",
    "\n",
    "Copyright (C) 2023 Commscope. All rights reserved.\n",
    "\n",
    "END OF TEST\n"
]

#
# First comment block is an Active Video copyright statement if one of the
# lines matches the following regular expression.
#
re_copyright = re.compile("copyright.+active.*video", re.I)

re_include = re.compile(".+")
# re_exclude = re.compile("^\b$") # Never matches.
re_exclude = re.compile("(^\..+$)|(.+\.(key|pem|png|jpg|jpeg|mp4|ts|pdf|rawdeflate)$)|third_party|third\-party|thirdparty")

#
# Add copyright if file does not start with a comment block?
#
add_copyright_c = False
add_copyright_java = False
add_copyright_js = False
add_copyright_hash = False
add_copyright_puml = False

#
# Analyze
#
re_skip_first_line = re.compile("(^#!\/bin)|(^@startuml)")

re_ext = re.compile("\.[^\.]+$");
re_ext_c = re.compile("^\.(cpp|cxx|c|hpp|hxx|h|glsl|frag|vert)$", re.I)
re_ext_java = re.compile("^\.(java)$", re.I)
re_ext_js = re.compile("^\.(js|javascript)$", re.I)
re_ext_hash = re.compile("^\.(py|sh|cmake|nut|yaml)$", re.I)
re_ext_puml = re.compile("^\.puml$", re.I)
re_ext_skip = re.compile("^\.(json|md|rst)$", re.I)

def analyze(filename):
    #
    # Get filename extension.
    #
    ext = re_ext.findall(filename)
    ext = ext[0] if len(ext) > 0 else ""

    if re_ext_skip.search(ext):
        print("{}: skipped".format(filename))
        return None

    #
    # Open file.
    #
    lines = []

    try:
        with open(filename, "r", encoding="UTF-8") as file:
            lines = file.readlines()
    except IOError as e:
        print("{}: failed to read ({})".format(filename, e.strerror))
        return None
    except:
        print("{}: not UTF-8 compatible (binary?)".format(filename))
        return None

    #
    # Find first non-blank line.
    #
    begin = 0
    end = len(lines)

    # Bail on empty files.
    if 0 == end:
        return None

    # Test to skip first line.
    if re_skip_first_line.search(lines[0]):
        begin = 1

    # Find start of first comment block.
    for begin in range(begin, end):
        if lines[begin].strip():
            break

    if begin >= end:
        print("{}: comment only file".format(filename))
        return None

    # Determine comment style and potential copyright comment.
    comment = None
    line = lines[begin].strip()
    cont = None
    term = None
    update = False

    if re_ext_c.search(ext):
        if line.startswith("/*"):
            comment = "/*"
            term = "*/"
        elif line.startswith("//"):
            comment = "//"
            cont = "//"
        elif ".c" == ext:
            comment = "/*"
            update = add_copyright_c
        else:
            comment = "//";
            update = add_copyright_c

    elif re_ext_java.search(ext):
        if line.startswith("/*"):
            comment = "/*"
            term = "*/"
        elif line.startswith("//"):
            comment = "//"
            cont = "//"
        else:
            comment = "//"
            update = add_copyright_java

    elif re_ext_js.search(ext):
        if line.startswith("/*"):
            comment = "/*"
            term = "*/"
        elif line.startswith("//"):
            comment = "//"
            cont = "//"
        else:
            comment = "//"
            update = add_copyright_js

    elif re_ext_hash.search(ext):
        comment = "#"
        if line.startswith("#"):
            cont = "#"
        else:
            update = add_copyright_hash

    elif re_ext_puml.search(ext):
        comment = "'"
        if line.startswith("'"):
            cont = "'"
        elif line.startswith("/'"):
            term = "'/"
        else:
            update = add_copyright_puml

    else:
        print("{}: no or unknown extension".format(filename))
        return None

    if not update:
        if cont:
            for end in range(begin, end):
                if re_copyright.search(lines[end]):
                    update = True
                if not lines[end].strip().startswith(cont):
                    end = end - 1
                    break
        elif term:
            for end in range(begin, end):
                if re_copyright.search(lines[end]):
                    update = True
                if lines[end].strip().endswith(term):
                    break
        else:
            end = begin
    else:
        begin = 0
        end = 0

    if not update:
        if begin < end:
            print("{}: other copyright owner".format(filename, update))
        else:
            print("{}: no comment, not added".format(filename))
        return None

    print("{}: update".format(filename))

    return {
        "name": filename,
        "comment": comment,
        "lines": lines,
        "begin": begin,
        "end": end
    }

def create_tmp(file):
    try:
        tmp = open(file["name"] + ".tmp", "w")
        lines = file["lines"]

        for i in range(0, file["begin"]):
            tmp.write(lines[i])

        comment = file["comment"]

        def write_line(comment, line):
            if line.strip():
                tmp.write(comment + " " + line)
            else:
                tmp.write(comment + "\n")

        if "/*" == comment:
            tmp.write("/*\n")
            for line in copyright:
                write_line(" *", line)
            tmp.write(" */\n")

        else:
            tmp.write(comment + "\n")
            for line in copyright:
                write_line(comment, line)
            tmp.write(comment + "\n")

        for i in range(file["end"] + 1, len(lines)):
            tmp.write(lines[i])

        tmp.close()

    except IOError as e:
        os.exit("{}: failed to write ({})".format(file["name"]), e.strerror)


def recurse(filename):
    if True == os.path.isdir(filename):
        for dir_entry in os.listdir(filename):
            if not re_include.match(dir_entry):
                print("{}: not included".format(filename + "/" + dir_entry))
                continue

            if re_exclude.match(dir_entry):
                print("{}: excluded".format(filename + "/" + dir_entry))
                continue
            recurse(filename + "/" + dir_entry)
        return

    file = analyze(filename)
    if not file:
        return

    create_tmp(file)

    os.rename(file["name"] + ".tmp", file["name"])

#
# Recurse over directories.
#
recurse(sys.argv[1])

