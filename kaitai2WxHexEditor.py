#!/usr/bin/env python3
import sys
from kaitaistruct import KaitaiStruct
from plumbum import cli
from pathlib import Path
from bs4 import BeautifulSoup, Tag
import typing
from reprlib import Repr, recursive_repr
import math
import random


def randColor():
	a = hex(random.randrange(0, 256))
	b = hex(random.randrange(0, 256))
	c = hex(random.randrange(0, 256))
	a = a[2:]
	b = b[2:]
	c = c[2:]
	if len(a) < 2:
		a = "0" + a
	if len(b) < 2:
		b = "0" + b
	if len(c) < 2:
		c = "0" + c
	z = a + b + c
	return "#" + z.upper()


rootElName = "wxHexEditor_XML_TAG"

id = 0


def createTag(name, start, end, fontColor, noteColor):
	global id
	tg = Tag(None, None, "TAG")
	tg.attrs["id"] = str(id)
	id += 1

	dic = {"start_offset": start, "end_offset": end, "font_colour": fontColor, "note_colour": noteColor, "tag_text": name}

	for k, v in dic.items():
		st = Tag(None, None, k)
		st.string = str(v)
		tg.append(st)
	return tg


# @recursive_repr()
def dumpStruct(s, root, prefix="", nest=False):
	if isinstance(s, list):
		for i, item in enumerate(s):
			dumpStruct(item, root, prefix + "[" + str(i) + "]")
	elif isinstance(s, KaitaiStruct):
		if hasattr(s, "_debug"):
			for name, descr in s._debug.items():
				prop = getattr(s, name)
				if not isinstance(prop, KaitaiStruct) or nest:
					root.append(createTag(prefix + "." + name, descr["start"], descr["end"], randColor(), randColor())) # WTF with signatures?
				#print("name", name)
				dumpStruct(prop, root, prefix + "." + name)
		if not nest:
			p = s._io.pos()
			rest = math.ceil(s._io.bits_left)
			#print(prefix, "p", p, "rest", rest)
			if rest:
				root.append(createTag(prefix + ".$rest", p, p + rest, randColor(), randColor()))


def createTags(parsed, filePath=None, nest=False):
	x = BeautifulSoup('<?xml version="1.0" encoding="UTF-8"?>\n<' + rootElName + "/>", "xml")
	x = x.select_one(rootElName)

	fn = Tag(None, None, "filename")
	fn.attrs["path"] = str(filePath)
	x.append(fn)

	dumpStruct(parsed, fn, nest=nest)
	return x

from kaitaiStructCompile.utils import KSCDirs, transformName

import kaitaiStructCompile.importer as ksimporter
from kaitaiStructCompile.defaults import subDirsNames
dirs = KSCDirs(subDirsNames, root=None)
ksimporter._importer._searchDirs = ksimporter._importer._searchDirs.__class__((".", dirs.formats))
ksimporter._importer.recursiveSearch = True

import importlib


import warnings

def importKSYSpec(specName:str, dir:Path=None):
	assert ksimporter is not None
	if dir:
		ksimporter._importer.searchDirs.append(dir)
	
	print("Importing "+ksimporter.KSYImporter.marker+"."+specName)
	m = __import__(ksimporter.KSYImporter.marker+"."+specName, globals(), locals(), ())
	resDict = getattr(ksimporter, specName).__dict__
	
	return resDict

class APPCLI(cli.Application):
	nest = cli.Flag("--nest", help="Create parent blocks. Don't use: it is just for my convenience")
	specDir = cli.SwitchAttr("--formatsDir", argtype=cli.ExistingDirectory, default=".", list=True, argname='DIR', help="a dir with KSY specs")
	
	def main(self, specName:str, fileName:str):
		if ksimporter is not None:
			for d in self.specDir:
				if d != ".":
					d = Path(d)
					ksimporter._importer.searchDirs.insert(0, d)
		else:
			warnings.warn("install kaitaiStructCompile with kaitaiStructCompile.importer!")
		
		if "." in specName: # assumme file name
			specPath = Path(specName).absolute()
			if specPath.is_file():
				specName = specPath.stem
				if specPath.suffix.lower() == ".ksy":
					specName = specPath.stem
					resDict = importKSYSpec(specName, specPath.parent)
				else: # assumme python module
					pathBackup=sys.path
					sys.path=list(sys.path)
					try:
						parentDir = specPath.parent
						sys.path.append(str(parentDir.parent.absolute()))
						source=specPath.read_text()
						resDict = ksimporter.KSYImporter._runCompiledCode(source, str(specPath), None, {"__builtins__":{"__import__": __import__}, "__name__": parentDir.name})
					finally:
						sys.path=pathBackup
			else:
				raise ValueError("No such file "+str(specPath))
		else:
			resDict = importKSYSpec(specName, None)
		
		className = transformName(specName, True)
		specClass = resDict[className]
		
		print("Spec class: ", specClass, file=sys.stderr)

		parsed = specClass.from_file(fileName)
		Path(str(fileName) + ".tags").write_text(str(createTags(parsed, fileName, nest=self.nest)))


if __name__ == "__main__":
	APPCLI.run()