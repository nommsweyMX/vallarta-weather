"""GOES-R ABI fixed-grid geometry: lat/lon -> scan angles, satellite view angles, parallax."""
import numpy as np, h5py

RE, RP = 6378137.0, 6356752.31414
E2 = (RE**2 - RP**2) / RE**2

def proj(h):
    p = h['goes_imager_projection'].attrs
    return float(p['perspective_point_height'][0]) + float(p['semi_major_axis'][0]), np.radians(float(p['longitude_of_projection_origin'][0]))

def axis(h, name):
    v = h[name]; return v[:] * float(v.attrs['scale_factor'][0]) + float(v.attrs['add_offset'][0])

def ll2xy(lat, lon, H, lam0):
    """geodetic lat/lon (deg) -> ABI scan angles x, y (rad)."""
    phi = np.radians(lat); lam = np.radians(lon)
    phc = np.arctan(RP**2 / RE**2 * np.tan(phi))
    rc = RP / np.sqrt(1 - E2 * np.cos(phc)**2)
    sx = H - rc * np.cos(phc) * np.cos(lam - lam0)
    sy = -rc * np.cos(phc) * np.sin(lam - lam0)
    sz = rc * np.sin(phc)
    return np.arcsin(-sy / np.sqrt(sx**2 + sy**2 + sz**2)), np.arctan(sz / sx)

def view(lat, lon, H, lam0):
    """satellite zenith angle (rad) and azimuth from the point toward the sub-satellite point (rad, clockwise from north), spherical approx."""
    phi = np.radians(lat); dl = lam0 - np.radians(lon)
    g = np.arccos(np.cos(phi) * np.cos(dl))                       # central angle point -> sub-satellite point
    R = 6371e3
    zen = np.arctan2(H * np.sin(g), H * np.cos(g) - R)           # angle at the point between local vertical and the satellite
    az = np.arctan2(np.sin(dl), -np.sin(phi) * np.cos(dl))        # toward the sub-satellite point (equator at lam0)
    return zen, az

def parallax_shift(lat, lon, hgt_m, H, lam0):
    """apparent (lat, lon) of a cloud top at height hgt above (lat, lon): displaced away from the satellite by h*tan(zen)."""
    zen, az = view(lat, lon, H, lam0)
    d = hgt_m * np.tan(zen)                                       # metres, away from the satellite
    dn, de = -d * np.cos(az), -d * np.sin(az)
    return lat + dn / 111.2e3, lon + de / (111.2e3 * np.cos(np.radians(lat)))
