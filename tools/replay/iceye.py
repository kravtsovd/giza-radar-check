import json, struct
import xml.etree.ElementTree as ET
import numpy as np
import slc_core as core
STEM = "ICEYE_STQ4S3_20250602T202139Z_4806740_X50_SLEDP_SLC"

class Iceye:
    """the COG stores mapped amplitude/phase, not signed I/Q."""

    def __init__(self, folder, stem=STEM, look_side='right'):
        metadata = json.loads((folder / (stem + ".json")).read_text())
        p = self.properties = metadata["properties"]
        self.f = stream = (folder / (stem + ".tif")).open("rb")
        if stream.read(8) != b"II+\x00\x08\x00\x00\x00":
            raise ValueError("Expected little-endian BigTIFF")
        stream.seek(struct.unpack("<Q", stream.read(8))[0])
        count = struct.unpack("<Q", stream.read(8))[0]
        entries = [struct.unpack("<HHQ8s", stream.read(20)) for _ in range(count)]
        types = {2: "u1", 3: "<u2", 4: "<u4", 12: "<f8", 16: "<u8"}
        self.tags = tags = {}
        for key, typ, n, raw in entries:
            if typ not in types:
                continue
            dtype = np.dtype(types[typ])
            size = n * dtype.itemsize
            if size > 8:
                stream.seek(int.from_bytes(raw, "little"))
                raw = stream.read(size)
            tags[key] = np.frombuffer(raw, dtype, n)
        for key, expected in {258: [16,16], 259: [1], 277: [2], 284: [1], 322: [512],
                              323: [512], 339: [1,1]}.items():
            np.testing.assert_array_equal(tags[key], expected)
        self.rows, self.cols = p["proj:shape"]
        assert [self.rows, self.cols] == [tags[257][0], tags[256][0]]
        self.spacing = np.array([p["sar:pixel_spacing_range"], p["sar:pixel_spacing_azimuth"]])
        self.im = dict(pixel_spacing_row=self.spacing[0], pixel_spacing_column=self.spacing[1], scale_factor=1)
        xml = ET.fromstring(tags[42112].tobytes().rstrip(b"\x00"))
        self.scales = []
        for band, name in enumerate(["AMPLITUDE", "PHASE"]):
            attrs = {m.attrib["name"]: m.text for m in xml.findall(f"Item[@sample='{band}']")}
            assert attrs["NAME"] == name
            self.scales.append((float(attrs["SCALE"]), float(attrs["OFFSET"])))
        self.mapping = p["iceye:amplitude_mapping"]
        assert self.mapping["function"] == "power"
        assert p["iceye:orientation"] == "shadows-down" and p["sar:observation_direction"] == look_side
        self.T = float((np.datetime64(p["end_datetime"][:-1])-np.datetime64(p["start_datetime"][:-1]))
                       / np.timedelta64(1, "s"))
        self.collect = {"start_timestamp":p["start_datetime"], "state":{"state_vectors":p["iceye:orbit_states"]}}
        self.fraction = p["iceye:processing_bandwidth_azimuth"] / p["iceye:processing_prf"]
        assert 0 < self.fraction <= 1

    rpc = core.Scene.rpc

    def read(self, origin, shape):
        row, col = map(int, origin)
        h, w = map(int, shape)
        if row < 0 or col < 0 or row+h > self.rows or col+w > self.cols:
            raise ValueError("SLC ROI outside product")
        result = np.empty((h,w), dtype=np.complex64)
        scale, exponent = (self.mapping["parameters"][k] for k in ("scale","exponent"))
        for tr in range(row//512, (row+h-1)//512+1):
            for tc in range(col//512, (col+w-1)//512+1):
                index = tr*((self.cols+511)//512)+tc
                self.f.seek(int(self.tags[324][index]))
                buf = self.f.read(int(self.tags[325][index]))
                tile = np.frombuffer(buf,"<u2").reshape(512,512,2)
                r0,r1 = max(row,tr*512),min(row+h,(tr+1)*512)
                c0,c1 = max(col,tc*512),min(col+w,(tc+1)*512)
                raw = tile[r0-tr*512:r1-tr*512,c0-tc*512:c1-tc*512,:].astype("f")
                amp = (raw[...,0]*self.scales[0][0]+self.scales[0][1])**(1/exponent)/scale
                phase = raw[...,1]*self.scales[1][0]+self.scales[1][1]
                result[r0-row:r1-row,c0-col:c1-col] = amp*np.exp(1j*phase)
        return result


