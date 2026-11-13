"""Metric geometric visibility, with opaque raster obstructions and spherical curvature."""
import math
import numpy as np
from numba import njit

@njit(cache=True)
def sightlines(terrain, surface, valid, ox, oy, observer_z, cell, max_range, smoke_height, radius):
    """Return [bare ground, bare smoke, obstructed ground, obstructed smoke] masks.

    ox/oy are fractional column/row coordinates (centres at n+0.5).
    Sample each ray at <= half a cell. Exclude observer/target cells along the
    ray; the target's own opaque surface explicitly blocks its ground target.
    Unknown intermediate cells invalidate all four targets. No refraction.
    """
    rows, cols = terrain.shape
    out = np.zeros((4, rows, cols), dtype=np.bool_)
    for row in range(rows):
        for col in range(cols):
            dx = col + .5 - ox
            dy = row + .5 - oy
            distance = math.sqrt(dx*dx+dy*dy)*cell
            if distance < cell*.5 or distance > max_range or not valid[row,col]:
                continue
            max_bare, max_surface = -1e30, -1e30
            steps = int(math.ceil(distance/(cell*.5)))
            last_r, last_c = -1, -1
            known = True
            for step in range(1, steps):
                f = step/steps
                rr, cc = int(oy+dy*f), int(ox+dx*f)
                if rr == row and cc == col:
                    continue
                if rr == int(oy) and cc == int(ox):
                    continue
                if rr == last_r and cc == last_c:
                    continue
                last_r, last_c = rr, cc
                if rr < 0 or rr >= rows or cc < 0 or cc >= cols or not valid[rr,cc]:
                    known = False
                    break
                # Use the sample distance with a cell-constant height.
                d = distance*f
                drop = d*d/(2*radius)
                max_bare = max(max_bare, (terrain[rr,cc]-observer_z-drop)/d)
                max_surface = max(max_surface, (surface[rr,cc]-observer_z-drop)/d)
            if not known:
                continue
            drop = distance*distance/(2*radius)
            ground_slope = (terrain[row,col]-observer_z-drop)/distance
            smoke_slope = (surface[row,col]+smoke_height-observer_z-drop)/distance
            out[0,row,col] = ground_slope >= max_bare-1e-9
            out[1,row,col] = smoke_slope >= max_bare-1e-9
            out[2,row,col] = ground_slope >= max_surface-1e-9 and surface[row,col] <= terrain[row,col]+.01
            out[3,row,col] = smoke_slope >= max_surface-1e-9
    return out

def frustum(dx, dy, dz, heading, tilt, hfov, vfov):
    """Rectilinear camera frustum. dx east, dy north; positive tilt is down."""
    yaw, pitch = np.radians(heading), np.radians(tilt)
    forward = dx*np.sin(yaw)*np.cos(pitch)+dy*np.cos(yaw)*np.cos(pitch)-dz*np.sin(pitch)
    right = dx*np.cos(yaw)-dy*np.sin(yaw)
    up = dx*np.sin(yaw)*np.sin(pitch)+dy*np.cos(yaw)*np.sin(pitch)+dz*np.cos(pitch)
    return (forward > 0) & (np.abs(right) <= forward*np.tan(np.radians(hfov/2))+1e-8) & (np.abs(up) <= forward*np.tan(np.radians(vfov/2))+1e-8)

def summarize(camera_masks, forest, water, eligible, cell_area, priority=None):
    """Each forest fraction counted once in the union, regardless of camera count."""
    counts = np.sum(camera_masks, axis=0) if len(camera_masks) else np.zeros(forest.shape,dtype=np.uint8)
    seen = (counts > 0) & eligible
    overlap = (counts >= 2) & eligible
    factor = cell_area/10000
    if priority is None:
        priority = np.zeros(forest.shape,dtype=bool)
    values = dict(visible_forest_ha=float(np.sum(forest*seen,dtype=np.float64)*factor),
                  blind_forest_ha=float(np.sum(forest*(eligible & ~seen),dtype=np.float64)*factor),
                  overlap_forest_ha=float(np.sum(forest*overlap,dtype=np.float64)*factor),
                  water_view_ha=float(np.sum(water*seen,dtype=np.float64)*factor),
                  priority_visible_ha=float(np.sum(forest*seen*priority,dtype=np.float64)*factor),
                  total_forest_ha=float(np.sum(forest*eligible,dtype=np.float64)*factor),
                  viewed_area_ha=float(np.count_nonzero(seen)*factor))
    values['water_share_pct'] = 100*values['water_view_ha']/values['viewed_area_ha'] if values['viewed_area_ha'] else 0
    return {k:round(v,3) for k,v in values.items()}, counts

def rank_candidates(results):
    return sorted(results, key=lambda r:(r['priority_visible_ha'],r['visible_forest_ha']),reverse=True)
