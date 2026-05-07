"""
Pure functions for computing satellite vegetation/water/SAR indices.

Used for both validation of values returned by Sentinel Hub and any
client-side computations needed (e.g., recomputing aggregates from raw bands).

All functions return 0.0 when their denominator would be zero, so callers
can treat them as total functions on float inputs.
"""
from __future__ import annotations

import math


# --------------------------------------------------------------------------- #
# Optical indices
# --------------------------------------------------------------------------- #

def compute_ndvi(nir: float, red: float) -> float:
    """
    Normalized Difference Vegetation Index.

    NDVI = (NIR - RED) / (NIR + RED)
    """
    denom = nir + red
    if denom == 0:
        return 0.0
    return (nir - red) / denom


def compute_evi(nir: float, red: float, blue: float) -> float:
    """
    Enhanced Vegetation Index (Sentinel-2 / Landsat coefficients).

    EVI = 2.5 * (NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1)
    """
    denom = nir + 6.0 * red - 7.5 * blue + 1.0
    if denom == 0:
        return 0.0
    return 2.5 * (nir - red) / denom


def compute_ndre(nir: float, red_edge: float) -> float:
    """
    Normalized Difference Red Edge index.

    NDRE = (NIR - RedEdge) / (NIR + RedEdge)
    """
    denom = nir + red_edge
    if denom == 0:
        return 0.0
    return (nir - red_edge) / denom


def compute_ndmi(nir: float, swir1: float) -> float:
    """
    Normalized Difference Moisture Index.

    NDMI = (NIR - SWIR1) / (NIR + SWIR1)
    """
    denom = nir + swir1
    if denom == 0:
        return 0.0
    return (nir - swir1) / denom


def compute_savi(nir: float, red: float, L: float = 0.5) -> float:
    """
    Soil-Adjusted Vegetation Index.

    SAVI = (1 + L) * (NIR - RED) / (NIR + RED + L)

    L is the soil-brightness correction factor (0 → NDVI, 1 → low veg cover;
    0.5 is the typical default for moderate cover).
    """
    denom = nir + red + L
    if denom == 0:
        return 0.0
    return (1.0 + L) * (nir - red) / denom


# --------------------------------------------------------------------------- #
# SAR
# --------------------------------------------------------------------------- #

def compute_sar_ratio_db(vv_db: float, vh_db: float) -> float:
    """
    Cross-pol / co-pol backscatter ratio in decibels.

    Linear ratio = VV / VH; in decibels this is just VV_db - VH_db.

    Returns 0.0 if either input is non-finite (NaN / inf).
    """
    if not (math.isfinite(vv_db) and math.isfinite(vh_db)):
        return 0.0
    return vv_db - vh_db


# --------------------------------------------------------------------------- #
# Evalscripts (Sentinel Hub V3)
# --------------------------------------------------------------------------- #

EVALSCRIPT_S2_OPTICAL_INDICES = """//VERSION=3
// Sentinel-2 L2A — NDVI, EVI, NDRE, NDMI, SAVI with SCL-based cloud mask.
function setup() {
  return {
    input: [{
      bands: ["B02", "B04", "B05", "B08", "B11", "SCL", "dataMask"],
      units: "REFLECTANCE"
    }],
    output: [
      { id: "ndvi",    bands: 1, sampleType: "FLOAT32" },
      { id: "evi",     bands: 1, sampleType: "FLOAT32" },
      { id: "ndre",    bands: 1, sampleType: "FLOAT32" },
      { id: "ndmi",    bands: 1, sampleType: "FLOAT32" },
      { id: "savi",    bands: 1, sampleType: "FLOAT32" },
      { id: "dataMask", bands: 1, sampleType: "UINT8" }
    ]
  };
}

function isCloud(scl) {
  // SCL classes treated as unusable:
  // 3 = cloud shadow, 8 = cloud medium prob, 9 = cloud high prob, 10 = thin cirrus
  return scl === 3 || scl === 8 || scl === 9 || scl === 10;
}

function safeDiv(num, den) {
  return den === 0 ? 0 : num / den;
}

function evaluatePixel(s) {
  var valid = s.dataMask === 1 && !isCloud(s.SCL);
  var mask = valid ? 1 : 0;

  var nir   = s.B08;
  var red   = s.B04;
  var blue  = s.B02;
  var rededge = s.B05;
  var swir1 = s.B11;
  var L = 0.5;

  var ndvi = safeDiv(nir - red, nir + red);
  var evi  = safeDiv(2.5 * (nir - red), nir + 6 * red - 7.5 * blue + 1);
  var ndre = safeDiv(nir - rededge, nir + rededge);
  var ndmi = safeDiv(nir - swir1, nir + swir1);
  var savi = safeDiv((1 + L) * (nir - red), nir + red + L);

  return {
    ndvi:    [valid ? ndvi : 0],
    evi:     [valid ? evi  : 0],
    ndre:    [valid ? ndre : 0],
    ndmi:    [valid ? ndmi : 0],
    savi:    [valid ? savi : 0],
    dataMask: [mask]
  };
}
"""


EVALSCRIPT_S1_SAR_BACKSCATTER = """//VERSION=3
// Sentinel-1 GRD — VV and VH backscatter in decibels.
function setup() {
  return {
    input: [{
      bands: ["VV", "VH", "dataMask"]
    }],
    output: [
      { id: "vv_db",    bands: 1, sampleType: "FLOAT32" },
      { id: "vh_db",    bands: 1, sampleType: "FLOAT32" },
      { id: "dataMask", bands: 1, sampleType: "UINT8" }
    ]
  };
}

function toDb(linear) {
  return linear > 0 ? 10 * Math.log(linear) / Math.LN10 : 0;
}

function evaluatePixel(s) {
  return {
    vv_db:    [toDb(s.VV)],
    vh_db:    [toDb(s.VH)],
    dataMask: [s.dataMask]
  };
}
"""
