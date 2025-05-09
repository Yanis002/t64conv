from dataclasses import dataclass
from pathlib import Path
import subprocess

@dataclass
class Texture64:
    magic: str
    nTypeROM: str
    unk_34: int
    nSizeX: int
    nSizeY: int
    eWrapS: int
    eWrapT: int
    nMode: int
    eFormat: int
    nAddress: int
    nCodePixel: int
    nCodeColor: int
    nData0: int
    nData1: int
    file_size: int
    data: bytes

    def to_tex0(self):
        data_l = bytearray(data)
        for i in range(0x00, 0x40):
            data_l[i] = 0x00
        data_l[0x00] = int.from_bytes("T".encode())
        data_l[0x01] = int.from_bytes("E".encode())
        data_l[0x02] = int.from_bytes("X".encode())
        data_l[0x03] = int.from_bytes("0".encode())
        data_l[0x0B] = 3
        data_l[0x13] = 0x40
        data_l[0x1D] = self.nSizeX
        data_l[0x1F] = self.nSizeY
        data_l[0x23] = self.eFormat
        if self.eFormat in {8, 9, 10}:
            data_l[0x1B] = 1
        return Texture0("TEX0", 0, 3, 0, 0x40, 0, 0, self.nSizeX, self.nSizeY, self.eFormat, 0, 0, 0, self.file_size, bytes(data_l))

@dataclass
class Texture0:
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
    file_size: int
    data: bytes

    def write(self):
        Path("./JP_wallwithredbird.TEX0").write_bytes(self.data)

data = Path("./JP_wallwithredbird.T64").read_bytes()
magic = data[0x00:0x04].decode()
if magic == "VC64":
    t64 = Texture64(
        magic,
        int.from_bytes(data[0x04:0x08]),
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
        len(data),
        data
    )

    tex0 = t64.to_tex0()
    tex0.write()
    subprocess.run(["./wimgt", "decode", "./JP_wallwithredbird.TEX0"])
else:
    print("tex0 to t64 not supported yet")
