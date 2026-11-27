"""Geographic transfer check from two real SLCs. See protocol.json before running."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy import ndimage



CENTER = np.array([29 + 58/60 + 45.05570/3600, 31 + 8/60 + 3.11209/3600])
# Four NGA grid posts capture the interpolation exactly.
GEOID_POSTS = [[15.500015258789062, 15.427773475646973], [15.383954048156738, 15.459442138671875]]
X = (CENTER[1] + 180)*4 % 1
Y = (90 - CENTER[0])*4 % 1
UNDULATION = np.array([1-Y, Y]) @ GEOID_POSTS @ np.array([1-X, X])
PAVEMENT = 60.4 + UNDULATION
SITES = {"King": ((-2.73558 + 7.74954)/2, (-13.6398 - 8.39724)/2, 3.0),
         "Queen": ((2.070862 + 7.8232)/2, (-2.63779 + 2.5908)/2, 1.5),
         "Subterranean": (6.58, -5.16, 90/43)}
EXPECTED_TIFF = {"20240916":"b000b40004e63fee4239bfbe2393d811c4bab5a3f72518dcb89e2853e4b92851",
                 "20241004":"9059f85c581ff9466a164c5f72894aa7fa840f334a7549abf139428d07fa1e88"}

def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def ring(radii, count):
    angles = np.arange(count)*2*np.pi/count
    directions = np.column_stack((np.cos(angles), np.sin(angles)))
    return np.vstack([radius*directions for radius in radii])

def geographic(en, height):
    # WGS84 local tangent approximation over less than 300 m.
    latitude = np.deg2rad(CENTER[0])
    w = 1 - .0066943799901413165*np.sin(latitude)**2
    metres_per_deg_n = np.pi/180 * 6378137 * (1 - .0066943799901413165) / w**1.5
    metres_per_deg_e = np.pi/180 * 6378137 * np.cos(latitude) / np.sqrt(w)
    return np.column_stack((CENTER[0] + en[:,1]/metres_per_deg_n,
                            CENTER[1] + en[:,0]/metres_per_deg_e, np.full(len(en), height)))

def compare(values):
    assert np.isfinite(values).all()
    return {"target": float(values[0]), "control_median": float(np.median(values[1:])),
            "beaten": int(np.count_nonzero(values[0] > values[1:])), "total": len(values)-1,
            "controls": values[1:].tolist()}

def surface(scene, height):
    """Contrast across a square's four edges, measured in the focused image."""
    translations = np.vstack(([0,0],ring((12,24,36,48),12)))
    normals = np.array([[1,0],[0,1],[-1,0],[0,-1]])
    edges = []
    for normal in normals:
        tangent = np.roll(normal,1)
        stations = np.linspace(-90,90,81)[:,None] * tangent
        sides = np.array([stations + (115.2 + dist)*normal for dist in (-3,+3)])
        edges.append(sides)
    xy = np.array(edges)[None] + translations[:,None,None,None,:]
    rc = scene.rpc(geographic(xy.reshape(-1,2), height))
    spacing = np.array([scene.im['pixel_spacing_row'], scene.im['pixel_spacing_column']])
    pad = np.ceil(5/spacing).astype(int) + 2
    start = np.floor(rc.min(axis=0)).astype(int) - pad
    stop = np.ceil(rc.max(axis=0)).astype(int) + pad
    chip = scene.read(start, stop-start)
    power = np.square(np.abs(chip) * scene.im['scale_factor'])
    smoothed = ndimage.gaussian_filter(power, sigma=1/spacing)
    sampled = ndimage.map_coordinates(smoothed, (rc-start).T, order=1)
    db = 10*np.log10(sampled.reshape(xy.shape[:-1]))
    edges = np.median(db[:,:,0] - db[:,:,1],axis=2)
    return {**compare(np.abs(edges).mean(axis=1)), "sides_signed_db_e_n_w_s": edges[0].tolist()}

