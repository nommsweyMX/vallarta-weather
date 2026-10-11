"""Terrain from AWS terrarium tiles: mosaic, resample to an equirectangular grid, hillshade, slope, watersheds."""
import glob, math, os, heapq, numpy as np
from PIL import Image

def mosaic(d, z):
    fs = glob.glob(f'{d}/{z}_*_*.png'); xs = sorted({int(f.split('_')[-2]) for f in fs}); ys = sorted({int(f.split('_')[-1][:-4]) for f in fs})
    A = np.zeros((len(ys) * 256, len(xs) * 256))
    for f in fs:
        x, y = int(f.split('_')[-2]), int(f.split('_')[-1][:-4])
        p = np.asarray(Image.open(f).convert('RGB')).astype(float)
        A[(y - ys[0]) * 256:(y - ys[0] + 1) * 256, (x - xs[0]) * 256:(x - xs[0] + 1) * 256] = p[..., 0] * 256 + p[..., 1] + p[..., 2] / 256 - 32768
    return A, xs[0], ys[0], z

def sample(M, lat, lon):
    """bilinear sample of a mercator mosaic at lat/lon arrays."""
    A, x0, y0, z = M; n = 2 ** z * 256
    px = (lon + 180) / 360 * n - x0 * 256 - 0.5
    r = np.radians(lat); py = (1 - np.log(np.tan(r) + 1 / np.cos(r)) / np.pi) / 2 * n - y0 * 256 - 0.5
    i = np.clip(np.floor(px).astype(int), 0, A.shape[1] - 2); j = np.clip(np.floor(py).astype(int), 0, A.shape[0] - 2)
    fx = np.clip(px - i, 0, 1); fy = np.clip(py - j, 0, 1)
    return (A[j, i] * (1 - fx) * (1 - fy) + A[j, i + 1] * fx * (1 - fy) + A[j + 1, i] * (1 - fx) * fy + A[j + 1, i + 1] * fx * fy)

def grid(lat0, lat1, lon0, lon1, ny, nx):
    la = np.linspace(lat0, lat1, ny)[:, None] * np.ones((1, nx)); lo = np.ones((ny, 1)) * np.linspace(lon0, lon1, nx)[None, :]
    return la, lo

def slope_aspect(E, dy_m, dx_m):
    gy, gx = np.gradient(E, dy_m, dx_m)            # rows run north->south
    return np.degrees(np.arctan(np.hypot(gx, gy))), gx, gy

def hillshade(E, dy_m, dx_m, az=315, alt=40, zf=1.6):
    gy, gx = np.gradient(E * zf, dy_m, dx_m)
    slope = np.arctan(np.hypot(gx, gy)); aspect = np.arctan2(-gx, gy)
    a, z = math.radians(360 - az + 90), math.radians(90 - alt)
    hs = np.cos(z) * np.cos(slope) + np.sin(z) * np.sin(slope) * np.cos(a - aspect)
    return np.clip(hs, 0, 1)

D8 = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]
def fill_and_flow(E, sea):
    """priority-flood pit filling from the sea / edges, then D8 receivers and flow accumulation (cell counts)."""
    ny, nx = E.shape; F = E.copy(); done = np.zeros(E.shape, bool); h = []
    for j in range(ny):
        for i in range(nx):
            if sea[j, i] or j in (0, ny - 1) or i in (0, nx - 1):
                heapq.heappush(h, (F[j, i], j, i)); done[j, i] = True
    rec = np.full(E.shape, -1, np.int64)
    while h:
        e, j, i = heapq.heappop(h)
        for dj, di in D8:
            a, b = j + dj, i + di
            if 0 <= a < ny and 0 <= b < nx and not done[a, b]:
                done[a, b] = True; F[a, b] = max(F[a, b], e + 1e-3); rec[a, b] = j * nx + i     # flows to the cell it was reached from
                heapq.heappush(h, (F[a, b], a, b))
    order = np.argsort(-F, axis=None)
    acc = np.ones(ny * nx); r = rec.ravel()
    for k in order:
        if r[k] >= 0: acc[r[k]] += acc[k]
    return F, r, acc.reshape(E.shape)

def upstream(rec, shape, outlet):
    """mask of cells draining to the outlet index."""
    ny, nx = shape; kids = {}
    for k, r in enumerate(rec):
        if r >= 0: kids.setdefault(int(r), []).append(k)
    m = np.zeros(ny * nx, bool); st = [outlet]
    while st:
        k = st.pop(); m[k] = True; st.extend(kids.get(k, []))
    return m.reshape(shape)
