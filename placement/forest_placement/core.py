"""Metric geometric visibility, with opaque raster obstructions and spherical curvature."""
import math
import numpy as np
from numba import njit

@njit(cache=True, nogil=True)
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

def camera_sector(dx, dy, dz, heading, tilt, hfov, vfov):
    """Product horizontal sector, with the existing tilted vertical field of view.

    The triangular housing is modelled as three adjoining 120° azimuth sectors,
    not three rectilinear lenses. Half-open seams assign each ray exactly once.
    Vertical geometry is evaluated in the ray's radial plane, independently of
    the horizontal seam. LOS, curvature, terrain and target heights are unchanged.
    """
    azimuth = np.degrees(np.arctan2(dx, dy)) % 360
    relative = np.round(azimuth - heading + hfov / 2, 10) % 360
    elevation = np.degrees(np.arctan2(dz, np.hypot(dx, dy)))
    return (relative < hfov) & (elevation >= -tilt-vfov/2) & (elevation <= -tilt+vfov/2)


def footprint_radii(dz, tilt, vfov, max_range, radius):
    """Annular guide on a level target plane through the launch cell.

    Solve elevation boundaries with the same curvature correction as the masks.
    Terrain-dependent boundaries are represented by the analysis raster itself.
    """
    cuts = [0., float(max_range)]
    for angle in (-tilt-vfov/2, -tilt+vfov/2):
        if -90 < angle < 90:
            roots = np.roots([1/(2*radius), np.tan(np.radians(angle)), -dz])
            cuts.extend(float(r.real) for r in roots if abs(r.imag) < 1e-8 and 0 < r.real < max_range)
    cuts = sorted(cuts)
    spans = []
    for lo, hi in zip(cuts, cuts[1:]):
        d = (lo+hi)/2
        elevation = np.degrees(np.arctan2(dz-d*d/(2*radius), d))
        if -tilt-vfov/2 <= elevation <= -tilt+vfov/2:
            spans.append((lo, hi))
    return spans

def summarize(camera_masks, forest, water, eligible, cell_area, priority=None, fov_masks=None):
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
    if fov_masks is not None:
        in_fov = np.any(fov_masks, axis=0) if len(fov_masks) else np.zeros(forest.shape, dtype=bool)
        values['outside_fov_forest_ha'] = float(np.sum(forest*(eligible & ~in_fov), dtype=np.float64)*factor)
        values['occluded_forest_ha'] = float(np.sum(forest*(eligible & in_fov & ~seen), dtype=np.float64)*factor)
    values['water_share_pct'] = 100*values['water_view_ha']/values['viewed_area_ha'] if values['viewed_area_ha'] else 0
    return {k:round(v,3) for k,v in values.items()}, counts

def rank_candidates(results):
    return sorted(results, key=lambda r:(r['priority_visible_ha'],r['visible_forest_ha']),reverse=True)
