import numpy as np

BUCKET = 10


class MarkField(object):
    """Pheromone marks of one kind. Each mark stores the step at which it expires,
    so nothing has to be decremented every step, and marks are grouped in square
    buckets so a lookup only looks at the marks near the ant."""

    def __init__(self):
        self.buckets = {}   # (bx, by) -> {(x, y): expiry step}, used by the lookups
        # The same marks in flat arrays, used to draw them all at once
        self.slot = {}      # (x, y) -> row in the arrays
        self.xs = np.empty(1024, dtype=np.int32)
        self.ys = np.empty(1024, dtype=np.int32)
        self.expiry = np.empty(1024, dtype=np.int64)
        self.n = 0

    def add(self, x, y, expiry):
        self.buckets.setdefault((x // BUCKET, y // BUCKET), {})[(x, y)] = expiry
        row = self.slot.get((x, y))
        if row is None:
            if self.n == len(self.xs):
                for name in ('xs', 'ys', 'expiry'):
                    old = getattr(self, name)
                    grown = np.empty(len(old) * 2, dtype=old.dtype)
                    grown[:self.n] = old[:self.n]
                    setattr(self, name, grown)
            row = self.n
            self.n += 1
            self.slot[(x, y)] = row
            self.xs[row], self.ys[row] = x, y
        self.expiry[row] = expiry

    def oldest_offset(self, px, py, r, now):
        """Offset (dx, dy) to the live mark closest to expiring inside the window
        -r <= dx < r, -r <= dy < r around (px, py), or None if there is none."""
        best = None
        best_expiry = float('inf')
        for bx in range((px - r) // BUCKET, (px + r - 1) // BUCKET + 1):
            for by in range((py - r) // BUCKET, (py + r - 1) // BUCKET + 1):
                bucket = self.buckets.get((bx, by))
                if not bucket:
                    continue
                for (mx, my), expiry in bucket.items():
                    if now < expiry < best_expiry and -r <= mx - px < r and -r <= my - py < r:
                        best_expiry = expiry
                        best = (mx - px, my - py)

        return best

    def positions(self, now):
        """Coordinates of the live marks as an (n, 2) array."""
        live = self.expiry[:self.n] > now
        return np.column_stack((self.xs[:self.n][live], self.ys[:self.n][live]))

    def prune(self, now):
        for key in list(self.buckets.keys()):
            bucket = self.buckets[key]
            for k in [k for k, expiry in bucket.items() if expiry <= now]:
                del bucket[k]
            if not bucket:
                del self.buckets[key]

        live = np.nonzero(self.expiry[:self.n] > now)[0]
        self.xs[:len(live)] = self.xs[live]
        self.ys[:len(live)] = self.ys[live]
        self.expiry[:len(live)] = self.expiry[live]
        self.n = len(live)
        self.slot = {(int(x), int(y)): row for row, (x, y) in enumerate(zip(self.xs[:self.n], self.ys[:self.n]))}

    def count(self, now):
        return int((self.expiry[:self.n] > now).sum())
