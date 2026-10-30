"""Frozen negotiation analysis. CLI reads economic rows only after the terminal gate."""
import argparse
import collections
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import platform
import sqlite3
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
WORKSTREAM = 'hq-negotiation-main-freeze-20261025'
BUYERS = ('neutral', 'firm', 'collaborative', 'programmed')
SELLERS = ('early', 'late', 'neutral_sol')
CATEGORIES = ('tradeoffs', 'narrow_zone', 'no_zone')
CONTRASTS = (('firm', 'neutral'), ('collaborative', 'neutral'),
             ('neutral', 'programmed'), ('firm', 'programmed'),
             ('collaborative', 'programmed'))
RULES = dict(scenarios=180, per_category=60, episodes=2160,
             replicates=10000, bootstrap_seed=20261025043,
             generator='PCG64', quantile_method='linear',
             practical_margin=5, decision_coverage=0.99,
             descriptive_coverage=0.95)
PRIOR_NANO = 7966240044


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def indexed(rows, key):
    out = {}
    for row in rows:
        value = row[key]
        require(isinstance(value, str) and value and value not in out,
                'Missing or duplicate ' + key)
        out[value] = row
    return out


def finite(value):
    require(type(value) in (int, float) and math.isfinite(value), 'Nonfinite numeric value')
    return value


def load_game(path):
    spec = importlib.util.spec_from_file_location('frozen_negotiation_game', path)
    game = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(game)
    return game


def interval(values, coverage):
    # Literal endpoints avoid floating subtraction changing quantile positions.
    endpoints = [0.005, 0.995] if coverage == .99 else [.025, .975]
    require(coverage in (.95, .99), 'Unapproved interval')
    return np.quantile(values, endpoints, method='linear').tolist()


def decision(point, ci):
    return dict(practically_promising=point >= 5 and ci[0] > 0,
                true_advantage_above_five=ci[0] > 5,
                equivalent=ci[0] >= -5 and ci[1] <= 5)


def bootstrap_indices():
    rng = np.random.Generator(np.random.PCG64(RULES['bootstrap_seed']))
    return np.stack([rng.integers(0, 60, size=(10000, 60)) for _ in CATEGORIES])


def estimate(cube, indices, categories=None, seller=None, mask=None):
    """cube is category x scenario x buyer x seller; indices shared by all views."""
    cats = list(range(3) if categories is None else categories)
    require(np.all(np.isfinite(cube)) and np.all(cube == np.rint(cube)),
            'Accepted game gains and paired differences must be integers')
    require(np.max(np.abs(cube)) <= 1000000, 'Integer aggregation safety bound exceeded')
    cube = cube.astype(np.int64)
    point_sums, draw_sums, point_counts, draw_counts = [], [], [], []
    seller_count = cube.shape[3] if seller is None else 1
    for c in cats:
        values = cube[c].sum(axis=2) if seller is None else cube[c, :, :, seller]
        keep = np.ones(60, dtype=bool) if mask is None else mask[c]
        require(keep.any(), 'Empty reporting stratum')
        point_sums.append(values[keep].sum(axis=0))
        point_counts.append(int(keep.sum()))
        sampled = values[indices[c]]
        weights = keep[indices[c]]
        totals = weights.sum(axis=1)
        require(np.all(totals > 0), 'Empty bootstrap subgroup; do not silently discard draws')
        draw_sums.append((sampled * weights[:, :, None]).sum(axis=1))
        draw_counts.append(totals)
    # Form one rational sum and divide once. The common-denominator form also
    # preserves equal category weights for first-mover draws whose counts differ.
    # With <=3 categories, <=60 rows, <=3 sellers and the guard above, all
    # intermediate numerators fit int64; accepted utility grids are far smaller.
    point_product = math.prod(point_counts)
    point_numerator = sum(s * (point_product // n) for s, n in zip(point_sums, point_counts))
    draw_product = np.prod(np.stack(draw_counts), axis=0, dtype=np.int64)
    draw_numerator = sum(s * (draw_product // n)[:, None] for s, n in zip(draw_sums, draw_counts))
    return (point_numerator / (len(cats) * seller_count * point_product),
            draw_numerator / (len(cats) * seller_count * draw_product)[:, None])


def paired_difference(left, right, ia, ib, indices, **view):
    # Subtract within each paired scenario before averaging, avoiding cancellation
    # of large arm means at an exact five-point decision boundary.
    delta = left[:, :, ia:ia+1, :] - right[:, :, ib:ib+1, :]
    point, draws = estimate(delta, indices, **view)
    return float(point[0]), draws[:, 0]


def contrasts(cube, indices, descriptive=False, **view):
    out = {}
    for a, b in CONTRASTS:
        ia, ib = BUYERS.index(a), BUYERS.index(b)
        d, sampled = paired_difference(cube, cube, ia, ib, indices, **view)
        row = dict(estimate=d, ci95=interval(sampled, .95))
        if not descriptive:
            row['ci99'] = interval(sampled, .99)
            row['operational_decision'] = decision(d, row['ci99'])
        out[a + '_minus_' + b] = row
    return out


