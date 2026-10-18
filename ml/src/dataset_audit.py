"""
CareConnect Dataset Audit Script
=================================
Audits three retinal image datasets (BRSET, mBRSET, ODIR-5K) independently.

For each dataset determines:
1.  Total image files on disk
2.  Unique patients and image records in metadata
3.  Image formats, dimensions, corrupted files, missing files
4.  Annotation schemas and available labels
5.  Label distributions (positive / negative counts)
6.  Missing labels, duplicate images, duplicate records
7.  Image-to-label mapping accuracy
8.  Suitability for CVD prediction task
9.  Cross-dataset patient/image overlap

Outputs saved to --output-dir (default: <dataset_root>/audit_reports/).

Usage:
    python dataset_audit.py --data-root "C:/Users/vinay/CVD Project"
"""

import argparse
import csv
import hashlib
import json
import os
import sys

# Ensure UTF-8 output even on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd
from PIL import Image

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MBRSET_FOLDER = "mbrset-a-mobile-brazilian-retinal-dataset-1.0-20261001T140750Z-1-001"
MBRSET_INNER = "mbrset-a-mobile-brazilian-retinal-dataset-1.0"
BRSET_FOLDER = "BRSET_v1.0.2-20261001T140733Z-1-006"
BRSET_INNER = "BRSET_v1.0.2"
ODIR_FOLDER = "ODIR-5K"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}

# Maximum images to sample for dimension/corruption checks (0 = all)
MAX_SAMPLE_FOR_DIMS = 0  # check all


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def find_csv_files(root: Path) -> List[Path]:
    """Recursively find all CSV files under root."""
    return sorted(root.rglob("*.csv"))


def find_image_files(root: Path) -> List[Path]:
    """Recursively find all image files under root."""
    files = []
    for f in sorted(root.rglob("*")):
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS:
            files.append(f)
    return files


def verify_image(path: Path) -> Dict[str, Any]:
    """
    Try to open an image and return metadata or error.
    Returns dict with keys: valid, width, height, format, mode, error
    """
    result = {"valid": False, "width": None, "height": None,
              "format": None, "mode": None, "error": None}
    try:
        with Image.open(path) as img:
            img.verify()  # checks for corruption without fully loading
        # Re-open to get dims (verify() may leave file in bad state)
        with Image.open(path) as img:
            result["width"] = img.width
            result["height"] = img.height
            result["format"] = img.format
            result["mode"] = img.mode
            result["valid"] = True
    except Exception as e:
        result["error"] = str(e)
    return result


def file_hash(path: Path, algorithm="md5", chunk_size=8192) -> str:
    """Compute hash of a file for duplicate detection."""
    h = hashlib.new(algorithm)
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def safe_int(val):
    """Safely convert to int, return None on failure."""
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# mBRSET Audit
# ---------------------------------------------------------------------------
def audit_mbrset(data_root: Path) -> Dict[str, Any]:
    """Full audit of the mBRSET dataset."""
    print("\n" + "=" * 70)
    print("AUDITING mBRSET DATASET")
    print("=" * 70)

    report = {"dataset": "mBRSET", "status": "auditing"}

    mbrset_root = data_root / MBRSET_FOLDER / MBRSET_INNER
    if not mbrset_root.exists():
        report["status"] = "not_found"
        report["error"] = f"mBRSET root not found: {mbrset_root}"
        print(f"  ERROR: {report['error']}")
        return report

    # 1. Find metadata CSV
    csv_path = mbrset_root / "labels_mbrset.csv"
    if not csv_path.exists():
        csvs = find_csv_files(mbrset_root)
        if csvs:
            csv_path = csvs[0]
        else:
            report["status"] = "no_metadata"
            report["error"] = "No CSV metadata found"
            return report

    print(f"  Metadata CSV: {csv_path}")
    df = pd.read_csv(csv_path, low_memory=False)
    report["metadata_csv"] = str(csv_path)
    report["metadata_columns"] = list(df.columns)
    report["metadata_rows"] = len(df)
    print(f"  Metadata rows: {len(df)}")

    # 2. Find image directory
    images_dir = mbrset_root / "images"
    if not images_dir.exists():
        # Try to find images elsewhere
        image_files = find_image_files(mbrset_root)
        images_dir = None
    else:
        image_files = find_image_files(images_dir)

    report["images_on_disk"] = len(image_files)
    print(f"  Images on disk: {len(image_files)}")

    # Build set of filenames on disk
    disk_filenames = {f.name for f in image_files}
    disk_filename_to_path = {f.name: f for f in image_files}

    # 3. Match metadata to images
    if "file" in df.columns:
        csv_filenames = set(df["file"].dropna().unique())
    elif "filename" in df.columns:
        csv_filenames = set(df["filename"].dropna().unique())
    else:
        csv_filenames = set()
        report["warning"] = "No 'file' or 'filename' column found in metadata"

    matched = csv_filenames & disk_filenames
    missing_on_disk = csv_filenames - disk_filenames
    extra_on_disk = disk_filenames - csv_filenames

    report["csv_unique_filenames"] = len(csv_filenames)
    report["matched_files"] = len(matched)
    report["missing_from_disk"] = len(missing_on_disk)
    report["extra_on_disk_no_label"] = len(extra_on_disk)
    report["missing_filenames"] = sorted(list(missing_on_disk))[:50]  # cap for readability

    print(f"  CSV unique filenames: {len(csv_filenames)}")
    print(f"  Matched (CSV <-> disk): {len(matched)}")
    print(f"  Missing from disk: {len(missing_on_disk)}")
    print(f"  Extra on disk (no label): {len(extra_on_disk)}")

    # 4. Patient analysis
    if "patient" in df.columns:
        df["patient_id"] = df["patient"].apply(safe_int)
        all_patients = df["patient_id"].dropna().unique()
        report["total_patients_in_csv"] = len(all_patients)

        # Patients with at least 1 image on disk
        df_with_image = df[df["file"].isin(disk_filenames)] if "file" in df.columns else df
        patients_with_images = df_with_image["patient_id"].dropna().unique()
        report["patients_with_images"] = len(patients_with_images)
        report["patients_without_images"] = len(set(all_patients) - set(patients_with_images))

        # Images per patient
        imgs_per_patient = df_with_image.groupby("patient_id")["file"].count()
        report["images_per_patient"] = {
            "mean": float(imgs_per_patient.mean()),
            "median": float(imgs_per_patient.median()),
            "min": int(imgs_per_patient.min()),
            "max": int(imgs_per_patient.max()),
        }
        print(f"  Total patients in CSV: {len(all_patients)}")
        print(f"  Patients with >= 1 image: {len(patients_with_images)}")
    else:
        report["patient_id_column"] = "not_found"

    # 5. Label analysis
    label_cols = {}

    # vascular_disease (primary CVD target)
    if "vascular_disease" in df.columns:
        vc = df["vascular_disease"].value_counts(dropna=False)
        label_cols["vascular_disease"] = {str(k): int(v) for k, v in vc.items()}
        # Patient-level
        if "patient_id" in df.columns:
            patient_vd = df.groupby("patient_id")["vascular_disease"].first()
            pvd_counts = patient_vd.value_counts(dropna=False)
            label_cols["vascular_disease_patient_level"] = {
                str(k): int(v) for k, v in pvd_counts.items()
            }
            # Check consistency (same label for all images of a patient)
            inconsistent = []
            for pid, grp in df.groupby("patient_id"):
                vals = grp["vascular_disease"].dropna().unique()
                if len(vals) > 1:
                    inconsistent.append(int(pid))
            label_cols["vascular_disease_inconsistent_patients"] = inconsistent

    # systemic_hypertension
    if "systemic_hypertension" in df.columns:
        vc = df["systemic_hypertension"].value_counts(dropna=False)
        label_cols["systemic_hypertension"] = {str(k): int(v) for k, v in vc.items()}
        if "patient_id" in df.columns:
            patient_ht = df.groupby("patient_id")["systemic_hypertension"].first()
            pht_counts = patient_ht.value_counts(dropna=False)
            label_cols["systemic_hypertension_patient_level"] = {
                str(k): int(v) for k, v in pht_counts.items()
            }

    # DR grades
    if "final_icdr" in df.columns:
        vc = df["final_icdr"].value_counts(dropna=False)
        label_cols["final_icdr"] = {str(k): int(v) for k, v in vc.items()}

    # Other clinical columns
    for col in ["acute_myocardial_infarction", "nephropathy", "neuropathy",
                "diabetic_foot", "obesity", "smoking", "alcohol_consumption",
                "insulin", "dm_time", "age", "sex"]:
        if col in df.columns:
            vc = df[col].value_counts(dropna=False)
            label_cols[f"{col}_distribution"] = {str(k): int(v) for k, v in vc.items()}

    report["label_analysis"] = label_cols

    # Print key label distributions
    if "vascular_disease" in df.columns:
        print(f"\n  Label: vascular_disease (image-level)")
        for k, v in sorted(label_cols.get("vascular_disease", {}).items()):
            print(f"    {k}: {v}")
        if "vascular_disease_patient_level" in label_cols:
            print(f"  Label: vascular_disease (patient-level)")
            for k, v in sorted(label_cols["vascular_disease_patient_level"].items()):
                print(f"    {k}: {v}")

    if "systemic_hypertension" in df.columns:
        print(f"\n  Label: systemic_hypertension (image-level)")
        for k, v in sorted(label_cols.get("systemic_hypertension", {}).items()):
            print(f"    {k}: {v}")

    # 6. Duplicate image check (by filename)
    file_counts = df["file"].value_counts() if "file" in df.columns else pd.Series()
    duplicate_filenames = file_counts[file_counts > 1]
    report["duplicate_filenames_in_csv"] = len(duplicate_filenames)
    if len(duplicate_filenames) > 0:
        report["duplicate_filename_examples"] = {
            str(k): int(v) for k, v in duplicate_filenames.head(10).items()
        }

    # 7. Image verification (sample or all)
    print(f"\n  Verifying image files...")
    corrupted = []
    dimensions = []
    formats = Counter()
    sample_files = image_files if MAX_SAMPLE_FOR_DIMS == 0 else image_files[:MAX_SAMPLE_FOR_DIMS]

    for i, img_path in enumerate(sample_files):
        if i % 500 == 0 and i > 0:
            print(f"    Checked {i}/{len(sample_files)} images...")
        info = verify_image(img_path)
        if not info["valid"]:
            corrupted.append({"file": img_path.name, "error": info["error"]})
        else:
            dimensions.append((info["width"], info["height"]))
            formats[info["format"]] += 1

    report["corrupted_images"] = corrupted
    report["corrupted_count"] = len(corrupted)
    report["image_formats"] = dict(formats)

    if dimensions:
        widths = [d[0] for d in dimensions]
        heights = [d[1] for d in dimensions]
        dim_counter = Counter(dimensions)
        report["image_dimensions"] = {
            "width_min": min(widths), "width_max": max(widths),
            "height_min": min(heights), "height_max": max(heights),
            "most_common_dimensions": [
                {"width": d[0], "height": d[1], "count": c}
                for d, c in dim_counter.most_common(5)
            ]
        }
        print(f"  Image dimensions -- W: {min(widths)}--{max(widths)}, H: {min(heights)}--{max(heights)}")

    print(f"  Corrupted images: {len(corrupted)}")
    print(f"  Image formats: {dict(formats)}")

    # 8. Quality and artifacts
    if "final_quality" in df.columns:
        quality_counts = df["final_quality"].value_counts(dropna=False)
        report["quality_distribution"] = {str(k): int(v) for k, v in quality_counts.items()}
    if "final_artifacts" in df.columns:
        artifact_counts = df["final_artifacts"].value_counts(dropna=False)
        report["artifact_distribution"] = {str(k): int(v) for k, v in artifact_counts.items()}

    report["status"] = "complete"
    return report


# ---------------------------------------------------------------------------
# BRSET Audit
# ---------------------------------------------------------------------------
def audit_brset(data_root: Path) -> Dict[str, Any]:
    """Full audit of the BRSET dataset (partial download)."""
    print("\n" + "=" * 70)
    print("AUDITING BRSET DATASET")
    print("=" * 70)

    report = {"dataset": "BRSET", "status": "auditing"}

    brset_root = data_root / BRSET_FOLDER / BRSET_INNER
    if not brset_root.exists():
        report["status"] = "not_found"
        report["error"] = f"BRSET root not found: {brset_root}"
        return report

    # Find all images
    image_files = find_image_files(brset_root)
    report["total_images_on_disk"] = len(image_files)
    print(f"  Total images found: {len(image_files)}")

    # Find all CSVs
    csv_files = find_csv_files(brset_root)
    report["csv_files_found"] = [str(f) for f in csv_files]
    report["csv_count"] = len(csv_files)
    print(f"  CSV files found: {len(csv_files)}")

    # Also check parent directory for labels
    parent_csvs = find_csv_files(data_root / BRSET_FOLDER)
    report["parent_csv_files"] = [str(f) for f in parent_csvs]

    # If any CSV is found, analyze it
    for csv_file in parent_csvs + csv_files:
        print(f"  Analyzing CSV: {csv_file.name}")
        try:
            df = pd.read_csv(csv_file, nrows=5, low_memory=False)
            report[f"csv_schema_{csv_file.name}"] = list(df.columns)
            report[f"csv_rows_{csv_file.name}"] = len(pd.read_csv(csv_file, low_memory=False))
        except Exception as e:
            report[f"csv_error_{csv_file.name}"] = str(e)

    # Find subdirectories with images
    image_dirs = set()
    for f in image_files:
        image_dirs.add(str(f.parent))
    report["image_directories"] = sorted(list(image_dirs))

    # Verify a sample of images
    corrupted = []
    dimensions = []
    formats = Counter()
    for img_path in image_files:
        info = verify_image(img_path)
        if not info["valid"]:
            corrupted.append({"file": str(img_path), "error": info["error"]})
        else:
            dimensions.append((info["width"], info["height"]))
            formats[info["format"]] += 1

    report["corrupted_images"] = corrupted
    report["corrupted_count"] = len(corrupted)
    report["image_formats"] = dict(formats)

    if dimensions:
        widths = [d[0] for d in dimensions]
        heights = [d[1] for d in dimensions]
        report["image_dimensions"] = {
            "width_min": min(widths), "width_max": max(widths),
            "height_min": min(heights), "height_max": max(heights),
        }
        print(f"  Dimensions -- W: {min(widths)}--{max(widths)}, H: {min(heights)}--{max(heights)}")

    # Assessment
    report["assessment"] = {
        "has_labels": len(csv_files) > 0 or len(parent_csvs) > 0,
        "is_complete_download": False,
        "shard_identifier": "-1-006 (single part of multi-part download)",
        "usable_for_supervised_cvd": False,
        "reason": f"Only {len(image_files)} images from a partial download shard. "
                  f"{'No' if len(csv_files) == 0 else len(csv_files)} label CSV(s) found within the extracted data."
    }

    report["status"] = "complete"
    print(f"  Corrupted: {len(corrupted)}")
    return report


# ---------------------------------------------------------------------------
# ODIR-5K Audit
# ---------------------------------------------------------------------------
def audit_odir5k(data_root: Path) -> Dict[str, Any]:
    """Full audit of the ODIR-5K dataset."""
    print("\n" + "=" * 70)
    print("AUDITING ODIR-5K DATASET")
    print("=" * 70)

    report = {"dataset": "ODIR-5K", "status": "auditing"}

    odir_root = data_root / ODIR_FOLDER
    if not odir_root.exists():
        report["status"] = "not_found"
        report["error"] = f"ODIR-5K root not found: {odir_root}"
        return report

    # 1. Find metadata
    full_df_path = odir_root / "full_df.csv"
    xlsx_path = odir_root / "ODIR-5K" / "ODIR-5K" / "data.xlsx"

    # Read full_df.csv
    if full_df_path.exists():
        df = pd.read_csv(full_df_path, low_memory=False)
        report["full_df_csv"] = str(full_df_path)
        report["full_df_rows"] = len(df)
        report["full_df_columns"] = list(df.columns)
        print(f"  full_df.csv: {len(df)} rows")
        print(f"  Columns: {list(df.columns)}")
    else:
        df = None
        report["full_df_csv"] = "not_found"

    # Read xlsx
    if xlsx_path.exists():
        try:
            df_xlsx = pd.read_excel(xlsx_path)
            report["data_xlsx_rows"] = len(df_xlsx)
            report["data_xlsx_columns"] = list(df_xlsx.columns)
            print(f"  data.xlsx: {len(df_xlsx)} rows")
        except Exception as e:
            report["data_xlsx_error"] = str(e)
            df_xlsx = None
    else:
        df_xlsx = None
        report["data_xlsx"] = "not_found"

    # 2. Find images
    preproc_dir = odir_root / "preprocessed_images"
    if preproc_dir.exists():
        image_files = find_image_files(preproc_dir)
    else:
        image_files = find_image_files(odir_root)

    report["images_on_disk"] = len(image_files)
    print(f"  Images on disk: {len(image_files)}")

    disk_filenames = {f.name for f in image_files}

    # 3. Match metadata to images
    if df is not None and "filename" in df.columns:
        csv_filenames = set(df["filename"].dropna().unique())
        matched = csv_filenames & disk_filenames
        missing = csv_filenames - disk_filenames
        extra = disk_filenames - csv_filenames

        report["csv_unique_filenames"] = len(csv_filenames)
        report["matched_files"] = len(matched)
        report["missing_from_disk"] = len(missing)
        report["extra_on_disk"] = len(extra)

        print(f"  Matched: {len(matched)}, Missing: {len(missing)}, Extra: {len(extra)}")

    # 4. Patient analysis
    if df is not None and "ID" in df.columns:
        patients = df["ID"].dropna().unique()
        report["total_patients"] = len(patients)
        print(f"  Total patients: {len(patients)}")

    # 5. Label analysis
    label_cols = {}
    disease_columns = ["N", "D", "G", "C", "A", "H", "M", "O"]
    disease_names = {
        "N": "Normal", "D": "Diabetes/DR", "G": "Glaucoma",
        "C": "Cataract", "A": "AMD", "H": "Hypertension (retinopathy)",
        "M": "Myopia", "O": "Other"
    }

    if df is not None:
        for col in disease_columns:
            if col in df.columns:
                vc = df[col].value_counts(dropna=False)
                label_cols[f"{col}_{disease_names.get(col, col)}"] = {
                    str(k): int(v) for k, v in vc.items()
                }

        # Patient-level analysis
        if "ID" in df.columns:
            patient_labels = {}
            for col in disease_columns:
                if col in df.columns:
                    patient_agg = df.groupby("ID")[col].max()
                    patient_labels[f"{col}_{disease_names.get(col, col)}_patient_level"] = {
                        str(k): int(v) for k, v in patient_agg.value_counts().items()
                    }
            label_cols.update(patient_labels)

        # Diagnostic keywords analysis
        if "Left-Diagnostic Keywords" in df.columns:
            all_keywords = []
            for kw in df["Left-Diagnostic Keywords"].dropna():
                all_keywords.extend([k.strip().lower() for k in str(kw).split(",")])
            if "Right-Diagnostic Keywords" in df.columns:
                for kw in df["Right-Diagnostic Keywords"].dropna():
                    all_keywords.extend([k.strip().lower() for k in str(kw).split(",")])
            kw_counts = Counter(all_keywords)
            # Look for CVD-related keywords
            cvd_keywords = {k: v for k, v in kw_counts.items()
                           if any(term in k for term in
                                  ["cardiovascular", "vascular", "heart",
                                   "myocardial", "coronary", "cvd", "angina",
                                   "stroke", "atheroscler"])}
            label_cols["cvd_related_diagnostic_keywords"] = cvd_keywords
            label_cols["top_20_diagnostic_keywords"] = dict(kw_counts.most_common(20))

    report["label_analysis"] = label_cols

    # Print label distributions
    for col in disease_columns:
        key = f"{col}_{disease_names.get(col, col)}"
        if key in label_cols:
            print(f"\n  Label: {key}")
            for k, v in sorted(label_cols[key].items()):
                print(f"    {k}: {v}")

    # 6. Image verification (sample for speed)
    print(f"\n  Verifying images...")
    corrupted = []
    dimensions = []
    formats = Counter()
    sample = image_files if len(image_files) <= 500 else image_files[:500]

    for i, img_path in enumerate(sample):
        if i % 200 == 0 and i > 0:
            print(f"    Checked {i}/{len(sample)}...")
        info = verify_image(img_path)
        if not info["valid"]:
            corrupted.append({"file": img_path.name, "error": info["error"]})
        else:
            dimensions.append((info["width"], info["height"]))
            formats[info["format"]] += 1

    report["sample_verified"] = len(sample)
    report["corrupted_in_sample"] = len(corrupted)
    report["image_formats"] = dict(formats)

    if dimensions:
        widths = [d[0] for d in dimensions]
        heights = [d[1] for d in dimensions]
        report["image_dimensions_sample"] = {
            "width_min": min(widths), "width_max": max(widths),
            "height_min": min(heights), "height_max": max(heights),
        }

    # 7. CVD label compatibility assessment
    report["cvd_compatibility"] = {
        "has_cvd_label": False,
        "has_vascular_disease_label": False,
        "has_hypertensive_retinopathy": "H" in df.columns if df is not None else False,
        "has_diabetes_retinopathy": "D" in df.columns if df is not None else False,
        "assessment": (
            "ODIR-5K contains ocular disease labels (N, D, G, C, A, H, M, O). "
            "The 'H' column indicates hypertensive retinopathy (an ocular finding), "
            "NOT systemic cardiovascular disease history. The 'D' column indicates "
            "diabetic retinopathy, NOT a diabetes diagnosis. "
            "There is NO cardiovascular disease (CVD) or vascular_disease label "
            "in ODIR-5K. Direct label mapping to mBRSET's vascular_disease target "
            "is NOT scientifically valid."
        ),
        "cvd_keywords_found_in_diagnoses": len(
            label_cols.get("cvd_related_diagnostic_keywords", {})
        ) > 0,
    }

    report["status"] = "complete"
    return report


# ---------------------------------------------------------------------------
# Cross-dataset analysis
# ---------------------------------------------------------------------------
def cross_dataset_analysis(mbrset_report: Dict, brset_report: Dict,
                           odir_report: Dict, data_root: Path) -> Dict[str, Any]:
    """Check for patient/image overlap across datasets."""
    print("\n" + "=" * 70)
    print("CROSS-DATASET OVERLAP ANALYSIS")
    print("=" * 70)

    report = {"analysis": "cross_dataset_overlap"}

    # mBRSET patient IDs
    mbrset_csv = data_root / MBRSET_FOLDER / MBRSET_INNER / "labels_mbrset.csv"
    mbrset_patients = set()
    if mbrset_csv.exists():
        df_m = pd.read_csv(mbrset_csv, usecols=["patient"], low_memory=False)
        mbrset_patients = set(df_m["patient"].dropna().unique())

    # ODIR-5K patient IDs
    odir_csv = data_root / ODIR_FOLDER / "full_df.csv"
    odir_patients = set()
    if odir_csv.exists():
        df_o = pd.read_csv(odir_csv, usecols=["ID"], low_memory=False)
        odir_patients = set(df_o["ID"].dropna().unique())

    # ID overlap (note: different ID namespaces, so numeric overlap is coincidental)
    numeric_overlap = mbrset_patients & odir_patients
    report["mbrset_patient_count"] = len(mbrset_patients)
    report["odir_patient_count"] = len(odir_patients)
    report["numeric_id_overlap"] = len(numeric_overlap)
    report["id_overlap_note"] = (
        "mBRSET and ODIR-5K use independent patient ID namespaces "
        "(different institutions, countries, and study designs). "
        "Numeric overlap of IDs is coincidental and does NOT indicate "
        "that the same physical patients appear in both datasets. "
        "Cross-dataset patient leakage is not a concern."
    )

    # Image filename overlap
    mbrset_images_dir = data_root / MBRSET_FOLDER / MBRSET_INNER / "images"
    odir_images_dir = data_root / ODIR_FOLDER / "preprocessed_images"
    brset_images_dir = (data_root / BRSET_FOLDER / BRSET_INNER /
                        "physionet.org" / "files" / "brazilian-ophthalmological" /
                        "1.0.2" / "fundus_photos")

    mbrset_fnames = set()
    odir_fnames = set()
    brset_fnames = set()

    if mbrset_images_dir.exists():
        mbrset_fnames = {f.name for f in mbrset_images_dir.iterdir() if f.is_file()}
    if odir_images_dir.exists():
        odir_fnames = {f.name for f in odir_images_dir.iterdir() if f.is_file()}
    if brset_images_dir.exists():
        brset_fnames = {f.name for f in brset_images_dir.iterdir() if f.is_file()}

    fname_overlap_mo = mbrset_fnames & odir_fnames
    fname_overlap_mb = mbrset_fnames & brset_fnames
    fname_overlap_ob = odir_fnames & brset_fnames

    report["filename_overlap"] = {
        "mbrset_vs_odir": len(fname_overlap_mo),
        "mbrset_vs_brset": len(fname_overlap_mb),
        "odir_vs_brset": len(fname_overlap_ob),
    }

    # BRSET and mBRSET share the same research group - check if BRSET images
    # might be a subset of mBRSET or vice versa
    if fname_overlap_mb:
        report["brset_mbrset_overlap_filenames"] = sorted(list(fname_overlap_mb))[:20]
        report["brset_mbrset_overlap_note"] = (
            "BRSET and mBRSET are from the same Brazilian research consortium. "
            "Filename overlap detected -- these may be the same retinal images. "
            "Patient-level deduplication is required if both are used for training."
        )

    print(f"  mBRSET patients: {len(mbrset_patients)}")
    print(f"  ODIR-5K patients: {len(odir_patients)}")
    print(f"  Numeric ID overlap: {len(numeric_overlap)} (coincidental)")
    print(f"  Filename overlap mBRSET <-> ODIR: {len(fname_overlap_mo)}")
    print(f"  Filename overlap mBRSET <-> BRSET: {len(fname_overlap_mb)}")
    print(f"  Filename overlap ODIR <-> BRSET: {len(fname_overlap_ob)}")

    return report


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------
def generate_reports(mbrset_report: Dict, brset_report: Dict,
                     odir_report: Dict, overlap_report: Dict,
                     output_dir: Path):
    """Generate all audit report files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n{'=' * 70}")
    print(f"GENERATING REPORTS  ->  {output_dir}")
    print(f"{'=' * 70}")

    # 1. dataset_summary.json
    summary = {
        "audit_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "datasets": {
            "mBRSET": {
                "status": mbrset_report.get("status"),
                "images_on_disk": mbrset_report.get("images_on_disk"),
                "metadata_rows": mbrset_report.get("metadata_rows"),
                "matched_files": mbrset_report.get("matched_files"),
                "missing_from_disk": mbrset_report.get("missing_from_disk"),
                "total_patients": mbrset_report.get("total_patients_in_csv"),
                "patients_with_images": mbrset_report.get("patients_with_images"),
                "corrupted_images": mbrset_report.get("corrupted_count"),
                "has_cvd_label": True,
                "usable_for_cvd_training": True,
            },
            "BRSET": {
                "status": brset_report.get("status"),
                "images_on_disk": brset_report.get("total_images_on_disk"),
                "has_labels": brset_report.get("assessment", {}).get("has_labels", False),
                "is_complete": False,
                "usable_for_cvd_training": False,
                "reason": brset_report.get("assessment", {}).get("reason", ""),
            },
            "ODIR-5K": {
                "status": odir_report.get("status"),
                "images_on_disk": odir_report.get("images_on_disk"),
                "metadata_rows": odir_report.get("full_df_rows"),
                "total_patients": odir_report.get("total_patients"),
                "has_cvd_label": False,
                "usable_for_cvd_training": False,
                "potential_use": "Retinal image pretraining or ocular disease classification",
                "reason": odir_report.get("cvd_compatibility", {}).get("assessment", ""),
            },
        },
        "cross_dataset": overlap_report,
    }
    with open(output_dir / "dataset_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)
    print("  [OK] dataset_summary.json")

    # 2. label_distribution.csv
    rows = []
    # mBRSET labels
    if "label_analysis" in mbrset_report:
        la = mbrset_report["label_analysis"]
        for label_name, dist in la.items():
            if isinstance(dist, dict) and "_distribution" not in label_name:
                for value, count in dist.items():
                    rows.append({
                        "dataset": "mBRSET",
                        "label": label_name,
                        "value": value,
                        "count": count,
                    })
    # ODIR labels
    if "label_analysis" in odir_report:
        la = odir_report["label_analysis"]
        for label_name, dist in la.items():
            if isinstance(dist, dict) and "keyword" not in label_name:
                for value, count in dist.items():
                    rows.append({
                        "dataset": "ODIR-5K",
                        "label": label_name,
                        "value": value,
                        "count": count,
                    })

    if rows:
        pd.DataFrame(rows).to_csv(output_dir / "label_distribution.csv", index=False)
    print("  [OK] label_distribution.csv")

    # 3. missing_files.csv
    missing_rows = []
    for fn in mbrset_report.get("missing_filenames", []):
        missing_rows.append({"dataset": "mBRSET", "filename": fn,
                            "reason": "Listed in metadata but not found on disk"})
    for item in mbrset_report.get("corrupted_images", []):
        missing_rows.append({"dataset": "mBRSET", "filename": item["file"],
                            "reason": f"Corrupted: {item['error']}"})
    for item in brset_report.get("corrupted_images", []):
        missing_rows.append({"dataset": "BRSET", "filename": item["file"],
                            "reason": f"Corrupted: {item['error']}"})

    pd.DataFrame(missing_rows).to_csv(output_dir / "missing_files.csv", index=False)
    print("  [OK] missing_files.csv")

    # 4. duplicate_report.csv
    dup_rows = []
    if "duplicate_filename_examples" in mbrset_report:
        for fn, count in mbrset_report["duplicate_filename_examples"].items():
            dup_rows.append({"dataset": "mBRSET", "filename": fn,
                            "occurrences_in_csv": count,
                            "note": "Same filename appears multiple times in metadata"})

    pd.DataFrame(dup_rows).to_csv(output_dir / "duplicate_report.csv", index=False)
    print("  [OK] duplicate_report.csv")

    # 5. patient_overlap_report.csv
    overlap_rows = []
    overlap_rows.append({
        "comparison": "mBRSET vs ODIR-5K",
        "overlap_type": "numeric_id_coincidental",
        "count": overlap_report.get("numeric_id_overlap", 0),
        "is_real_overlap": False,
        "note": overlap_report.get("id_overlap_note", ""),
    })
    fn_overlap = overlap_report.get("filename_overlap", {})
    for pair, count in fn_overlap.items():
        overlap_rows.append({
            "comparison": pair,
            "overlap_type": "filename",
            "count": count,
            "is_real_overlap": count > 0,
            "note": "Filename collision detected" if count > 0 else "No overlap",
        })

    pd.DataFrame(overlap_rows).to_csv(output_dir / "patient_overlap_report.csv", index=False)
    print("  [OK] patient_overlap_report.csv")

    # 6. Full detailed reports (JSON)
    with open(output_dir / "mbrset_full_audit.json", "w", encoding="utf-8") as f:
        json.dump(mbrset_report, f, indent=2, default=str)
    with open(output_dir / "brset_full_audit.json", "w", encoding="utf-8") as f:
        json.dump(brset_report, f, indent=2, default=str)
    with open(output_dir / "odir5k_full_audit.json", "w", encoding="utf-8") as f:
        json.dump(odir_report, f, indent=2, default=str)
    print("  [OK] mbrset_full_audit.json")
    print("  [OK] brset_full_audit.json")
    print("  [OK] odir5k_full_audit.json")

    # 7. audit_report.md
    generate_markdown_report(mbrset_report, brset_report, odir_report,
                             overlap_report, output_dir)


def generate_markdown_report(mbrset: Dict, brset: Dict, odir: Dict,
                             overlap: Dict, output_dir: Path):
    """Generate human-readable audit_report.md."""
    lines = []
    lines.append("# CareConnect Dataset Audit Report")
    lines.append(f"\n**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Audit Script:** `ml/src/dataset_audit.py`\n")

    # Summary table
    lines.append("## Executive Summary\n")
    lines.append("| Dataset | Images | Patients | CVD Label | Usable for CVD? |")
    lines.append("|:--|:--:|:--:|:--:|:--:|")

    m_imgs = mbrset.get("images_on_disk", "?")
    m_pats = mbrset.get("patients_with_images", "?")
    lines.append(f"| mBRSET | {m_imgs} | {m_pats} |   vascular_disease |   Yes |")

    b_imgs = brset.get("total_images_on_disk", "?")
    lines.append(f"| BRSET | {b_imgs} | ? (no labels) |   None |   No |")

    o_imgs = odir.get("images_on_disk", "?")
    o_pats = odir.get("total_patients", "?")
    lines.append(f"| ODIR-5K | {o_imgs} | {o_pats} |   None |   No (ocular only) |")

    # mBRSET detail
    lines.append("\n## 1. mBRSET (Primary Dataset)\n")
    lines.append(f"- **Metadata CSV rows:** {mbrset.get('metadata_rows', '?')}")
    lines.append(f"- **Images on disk:** {mbrset.get('images_on_disk', '?')}")
    lines.append(f"- **Matched (CSV <-> disk):** {mbrset.get('matched_files', '?')}")
    lines.append(f"- **Missing from disk:** {mbrset.get('missing_from_disk', '?')}")
    lines.append(f"- **Corrupted images:** {mbrset.get('corrupted_count', '?')}")
    lines.append(f"- **Total patients in CSV:** {mbrset.get('total_patients_in_csv', '?')}")
    lines.append(f"- **Patients with >=1 image:** {mbrset.get('patients_with_images', '?')}")

    la = mbrset.get("label_analysis", {})
    if "vascular_disease_patient_level" in la:
        lines.append("\n### Vascular Disease (Patient-Level)")
        lines.append("| Value | Count |")
        lines.append("|:--:|:--:|")
        for k, v in sorted(la["vascular_disease_patient_level"].items()):
            lines.append(f"| {k} | {v} |")

    if "systemic_hypertension_patient_level" in la:
        lines.append("\n### Systemic Hypertension (Patient-Level)")
        lines.append("| Value | Count |")
        lines.append("|:--:|:--:|")
        for k, v in sorted(la["systemic_hypertension_patient_level"].items()):
            lines.append(f"| {k} | {v} |")

    if "final_icdr" in la:
        lines.append("\n### Diabetic Retinopathy ICDR Grade (Image-Level)")
        lines.append("| Grade | Count |")
        lines.append("|:--:|:--:|")
        for k, v in sorted(la["final_icdr"].items()):
            lines.append(f"| {k} | {v} |")

    if "vascular_disease_inconsistent_patients" in la:
        incon = la["vascular_disease_inconsistent_patients"]
        lines.append(f"\n**Inconsistent vascular_disease across images of same patient:** {len(incon)}")

    # BRSET detail
    lines.append("\n## 2. BRSET (Incomplete Download)\n")
    lines.append(f"- **Images found:** {brset.get('total_images_on_disk', '?')}")
    lines.append(f"- **CSV files found:** {brset.get('csv_count', '?')}")
    assessment = brset.get("assessment", {})
    lines.append(f"- **Complete download:** {assessment.get('is_complete_download', '?')}")
    lines.append(f"- **Usable for CVD:** {assessment.get('usable_for_supervised_cvd', '?')}")
    lines.append(f"- **Reason:** {assessment.get('reason', 'N/A')}")

    # ODIR-5K detail
    lines.append("\n## 3. ODIR-5K\n")
    lines.append(f"- **Images on disk:** {odir.get('images_on_disk', '?')}")
    lines.append(f"- **Metadata rows:** {odir.get('full_df_rows', '?')}")
    lines.append(f"- **Total patients:** {odir.get('total_patients', '?')}")

    cvd_compat = odir.get("cvd_compatibility", {})
    lines.append(f"\n### CVD Label Compatibility")
    lines.append(f"- **Has CVD label:** {cvd_compat.get('has_cvd_label', '?')}")
    lines.append(f"- **Has vascular_disease:** {cvd_compat.get('has_vascular_disease_label', '?')}")
    lines.append(f"- **Assessment:** {cvd_compat.get('assessment', 'N/A')}")

    # Cross-dataset
    lines.append("\n## 4. Cross-Dataset Overlap\n")
    fn_overlap = overlap.get("filename_overlap", {})
    lines.append("| Comparison | Filename Overlap |")
    lines.append("|:--|:--:|")
    for pair, count in fn_overlap.items():
        lines.append(f"| {pair} | {count} |")
    lines.append(f"\n{overlap.get('id_overlap_note', '')}")

    # Recommendations
    lines.append("\n## 5. Recommendations\n")
    lines.append("1. **Primary training dataset:** mBRSET with `vascular_disease` as the CVD target")
    lines.append("2. **BRSET:** Cannot be used -- incomplete download with no labels")
    lines.append("3. **ODIR-5K:** Cannot provide CVD labels -- only suitable for:")
    lines.append("   - Retinal image pretraining (self-supervised or ImageNet-style)")
    lines.append("   - Separate ocular disease classification task")
    lines.append("   - Multi-task learning with separate ODIR-specific heads")
    lines.append("4. **Missing mBRSET images:** 1,162 metadata rows lack corresponding images -- "
                 "exclude from training but document the exclusion")
    lines.append("5. **Investigate baseline metrics:** CVD AUC 0.56 and HT AUC 0.46 suggest "
                 "potential label errors, preprocessing bugs, or fundamental signal weakness")

    with open(output_dir / "audit_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("  [OK] audit_report.md")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="CareConnect Dataset Audit")
    parser.add_argument("--data-root", type=str, required=True,
                        help="Root directory containing BRSET, mBRSET, ODIR-5K folders")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Output directory for reports (default: <data-root>/audit_reports)")
    args = parser.parse_args()

    data_root = Path(args.data_root)
    if not data_root.exists():
        print(f"ERROR: Data root not found: {data_root}")
        sys.exit(1)

    output_dir = Path(args.output_dir) if args.output_dir else data_root / "audit_reports"

    print(f"CareConnect Dataset Audit")
    print(f"Data root: {data_root}")
    print(f"Output dir: {output_dir}")

    # Run audits
    mbrset_report = audit_mbrset(data_root)
    brset_report = audit_brset(data_root)
    odir_report = audit_odir5k(data_root)
    overlap_report = cross_dataset_analysis(mbrset_report, brset_report,
                                             odir_report, data_root)

    # Generate all reports
    generate_reports(mbrset_report, brset_report, odir_report,
                     overlap_report, output_dir)

    print(f"\n{'=' * 70}")
    print(f"AUDIT COMPLETE")
    print(f"Reports saved to: {output_dir}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
