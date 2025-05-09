#!/usr/bin/env python3

import argparse
import struct
import subprocess
import sys

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


TODO_FIGURE_OUT = 0
OUTPUT_FOLDER = Path("output/").resolve()

@dataclass
class FileInfos:
    path: Path
    size: int
    data: Optional[bytes]


@dataclass
class Texture64:
    infos: FileInfos
    magic: str
    nTypeROM: Optional[str]
    unk_34: int
    nSizeX: int
    nSizeY: int
    eWrapS: int
    eWrapT: int
    nMode: int
    eFormat: int

    # VRAM address & 0xFFFF of the texture symbol
    # example with the rusty switch:
    # - symbol=gameplay_dangeon_keepTex_00D8A0
    # - `./sym_info.py -v gc-jp gameplay_dangeon_keepTex_00D8A0` returns `VRAM: 0x0500D8A0`
    # then nAddress should be set to 0xD8A0
    nAddress: int 

    nCodePixel: int
    nCodeColor: int
    nData0: int
    nData1: int
    palette_len: int
    palette_data: bytes
    data_len: int
    data: bytes

    def to_tex0(self):
        return Texture0(
            FileInfos(self.infos.path.with_suffix(".tex0"), self.infos.size, self.data), 
            "TEX0", 
            0,
            3,
            0,
            0x40,
            0,
            self.eFormat in {8, 9, 10},
            self.nSizeX,
            self.nSizeY,
            self.eFormat,
            0,
            0.0,
            0.0,
        )

    def to_bytes(self):
        return (
            self.magic.encode()
            + self.nTypeROM.encode()
            + f"{self.unk_34:04X}".encode()
            + f"{self.nSizeX:04X}".encode()
            + f"{self.nSizeY:04X}".encode()
            + f"{self.eWrapS:04X}".encode()
            + f"{self.eWrapT:04X}".encode()
            + f"{self.nMode:04X}".encode()
            + f"{self.eFormat:04X}".encode()
            + f"{self.nAddress:04X}".encode()
            + f"{self.nCodePixel:04X}".encode()
            + f"{self.nCodeColor:04X}".encode()
            + f"{self.nData0:04X}".encode()
            + f"{self.nData1:04X}".encode()
        )
    
    @staticmethod
    def from_bytes(path: Path):
        data = path.read_bytes()
        pal_len = int.from_bytes(data[0x38:0x3C]) * 2
        if pal_len != 0:
            data_len = int.from_bytes(data[pal_len:pal_len + 4])
        else:
            data_len = int.from_bytes(data[0x3C:0x40])
        return Texture64(
            FileInfos(path, len(data), data),
            data[0x00:0x04].decode(),
            data[0x04:0x08].decode(),
            int.from_bytes(data[0x08:0x0C]),
            int.from_bytes(data[0x0C:0x10]),
            int.from_bytes(data[0x10:0x14]),
            int.from_bytes(data[0x14:0x18]),
            int.from_bytes(data[0x18:0x1C]),
            int.from_bytes(data[0x1C:0x20]),
            int.from_bytes(data[0x20:0x24]),
            int.from_bytes(data[0x24:0x28]),
            int.from_bytes(data[0x28:0x2C]),
            int.from_bytes(data[0x2C:0x30]),
            int.from_bytes(data[0x30:0x34]),
            int.from_bytes(data[0x34:0x38]),
            pal_len,
            data[0x3C:pal_len] if pal_len != 0 else bytes(),
            data_len,
            data[pal_len:] if pal_len != 0 else data[0x40:],
        )
    
    def write_tex0(self):
        self.to_tex0().write_bytes()

    def write_bytes(self):
        stem = Path(self.infos.path.stem)
        out_path = OUTPUT_FOLDER / stem
        out_path.mkdir(exist_ok=True)
        (out_path / stem.with_suffix(self.infos.path.suffix)).write_bytes(self.to_bytes())


@dataclass
class Texture0:
    infos: FileInfos
    magic: str
    file_length: int
    version: int
    offset_brres: int
    offset_sections: int
    offset_filename_sub: int
    ci_flag: int
    nSizeX: int
    nSizeY: int
    eFormat: int
    nMipMap: int
    mipmap_min: float
    mipmap_max: float

    def to_t64(self, address: int):
        return Texture64(
            FileInfos(self.infos.path.with_suffix(".t64"), self.infos.size, None),
            "VC64",
            None,
            0,
            self.nSizeX,
            self.nSizeY,
            TODO_FIGURE_OUT,
            TODO_FIGURE_OUT,
            0x2000,
            self.eFormat,
            address,
            TODO_FIGURE_OUT,
            TODO_FIGURE_OUT,
            TODO_FIGURE_OUT,
            TODO_FIGURE_OUT,
            TODO_FIGURE_OUT,
            bytes(),
            TODO_FIGURE_OUT,
            bytes()
        )

    def to_bytes(self):
        header = (
            self.magic.encode()
            + self.file_length.to_bytes(4)
            + self.version.to_bytes(4)
            + self.offset_brres.to_bytes(4)
            + self.offset_sections.to_bytes(4)
            + self.offset_filename_sub.to_bytes(4)
            + self.ci_flag.to_bytes(4)
            + self.nSizeX.to_bytes(2)
            + self.nSizeY.to_bytes(2)
            + self.eFormat.to_bytes(4)
            + self.nMipMap.to_bytes(4)
            + bytes(struct.pack("f", self.mipmap_min))
            + bytes(struct.pack("f", self.mipmap_max))
        )

        # align to 64
        data = bytearray(header)
        while len(data) % 64:
            data.append(0)
        data.extend(bytearray(self.infos.data))

        return bytes(data)

    def write_t64(self, address: int):
        self.to_t64(address).write_bytes()

    def write_bytes(self):
        stem = Path(self.infos.path.stem)
        out_path = OUTPUT_FOLDER / stem
        out_path.mkdir(exist_ok=True)
        (out_path / stem.with_suffix(self.infos.path.suffix)).write_bytes(self.to_bytes())


def t64conv(path: Path, to_png: bool=False):
    if not path.exists():
        print(f"ERROR: path '{path}' don't exist!")
        sys.exit(1)

    t64 = Texture64.from_bytes(path)

    if t64.palette_len != 0:
        print(f"WARNING: CI textures are not supported yet, ignoring. ({path})")
        return

    tex0 = t64.to_tex0()
    tex0.write_bytes()

    if to_png:
        stem = Path(tex0.infos.path.stem)
        out_path = OUTPUT_FOLDER / stem / stem.with_suffix(tex0.infos.path.suffix)
        print(" ".join(["./wimgt", "decode", str(out_path), "-d", str(out_path.with_suffix(".png"))]))
        subprocess.run(["./wimgt", "decode", str(out_path), "-d", str(out_path.with_suffix(".png"))])


def main():
    global OUTPUT_FOLDER

    parser = argparse.ArgumentParser(description="Tool to convert T64 files to TEX0 format and can convert back to PNG.")
    parser.add_argument("file", nargs="?", help="Path to the base file")
    parser.add_argument("-m", "--mode", dest="mode", help="Operating mode, either 'T64' (to TEX0) or 'TEX0' (to T64), case doesn't matter.", required=False)
    parser.add_argument("-p", "--to_png", dest="to_png", action="store_true", help="Convert file to PNG", required=False, default=True)
    parser.add_argument("-o", "--output", dest="output", help="Set output folder", required=False, default=OUTPUT_FOLDER)
    parser.add_argument("-f", "--folder", dest="folder", help="Process all T64 files from provided folder", required=False)

    args = parser.parse_args()

    if args.output is not None:
        OUTPUT_FOLDER = Path(args.output).resolve()

    OUTPUT_FOLDER.mkdir(exist_ok=True)

    if args.file is not None:
        try:
            path = Path(args.file).resolve()
        except:
            print("ERROR: something went wrong...")
            sys.exit(1)

        if not path.exists():
            print(f"ERROR: path '{path}' don't exist!")
            sys.exit(1)

        if args.mode is not None:
            match args.mode.lower():
                case "t64":
                    t64conv(path)
                case "tex0":
                    print("ERROR: not supported yet.")
                    sys.exit(1)
                case _:
                    print(f"ERROR: operating mode not supported: '{args.mode}'")
                    sys.exit(0)
        elif args.to_png:
            t64conv(path, True)
    elif args.folder is not None:
        in_dir = Path(args.folder).resolve()

        if not in_dir.exists():
            print(f"ERROR: path '{in_dir}' don't exist!")
            sys.exit(1)

        t64_to_process: list[Path] = []
        for dirpath, dirnames, filenames in in_dir.walk():
            for filename in filenames:
                if filename.endswith(".T64"):
                    t64_to_process.append(Path(dirpath) / filename)

        for t64_path in t64_to_process:
            t64conv(t64_path, True)


if __name__ == "__main__":
    main()
