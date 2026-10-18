"""
CareConnect Retinal AI Data Pipeline: Preparation and Manifest Generation
========================================================================
- Ingests mBRSET metadata and physically verifies images on disk.
- Generates reproducible, zero-leakage patient-level splits (Train, Val, Test).
- Uses STRICT pure 'vascular_disease' target (no AMI conflation).
- Documents every single exclusion in audit_exclusions.csv.
- Stores project-relative paths (portable across machines).

Usage:
    python prepare_data.py --data-root "C:/Users/vinay/CVD Project"
    python prepare_data.py --data-root "../CVD Project" --output-dir "ml/datasets"
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit, ShuffleSplit


MBRSET_SUBDIR = Path("mbrset-a-mobile-brazilian-retinal-dataset-1.0-20261001T140750Z-1-001") / "mbrset-a-mobile-brazilian-retinal-dataset-1.0"


def find_mbrset_paths(data_root: Path) -> Tuple[Path, Path]:
    """Locate labels_mbrset.csv and images directory under data_root."""
    candidate_csv = data_root / MBRSET_SUBDIR / "labels_mbrset.csv"
    candidate_img = data_root / MBRSET_SUBDIR / "images"

    if candidate_csv.exists() and candidate_img.exists():
        return candidate_csv, candidate_img

    # Fallback: search recursively
    csvs = list(data_root.rglob("labels_mbrset.csv"))
    if not csvs:
        raise FileNotFoundError(f"labels_mbrset.csv not found under {data_root}")
    csv_path = csvs[0]
    img_dir = csv_path.parent / "images"
    if not img_dir.exists():
        raise FileNotFoundError(f"images directory not found next to {csv_path}")

    return csv_path, img_dir


def generate_manifest_and_exclusions(
    csv_path: Path,
    img_dir: Path,
    output_dir: Path,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Reconcile metadata against images on disk, generate dataset_manifest.csv
    and audit_exclusions.csv.
    """
    df_raw = pd.read_csv(csv_path, low_memory=False)
    print(f"[PrepareData] Loaded raw metadata: {len(df_raw)} records, {df_raw['patient'].nunique()} unique patients")

    # Get set of actual image files on disk
    disk_images = {f.name: f for f in img_dir.iterdir() if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png"]}
    print(f"[PrepareData] Verified images physically on disk: {len(disk_images)}")

    manifest_rows = []
    exclusion_rows = []

    # Track patient-level image counts
    files_per_patient = df_raw.groupby("patient")["file"].apply(list).to_dict()

    for idx, row in df_raw.iterrows():
        patient_id = int(float(row["patient"]))
        fname = str(row["file"]).strip()

        # Check if file exists on disk
        file_exists = fname in disk_images

        # Check label availability
        vd_val = row.get("vascular_disease")
        vd_valid = pd.notna(vd_val) and str(vd_val).strip() != "" and float(vd_val) in [0.0, 1.0]

        ht_val = row.get("systemic_hypertension")
        ht_valid = pd.notna(ht_val) and str(ht_val).strip() != "" and float(ht_val) in [0.0, 1.0]

        icdr_val = row.get("final_icdr")
        icdr_valid = pd.notna(icdr_val) and str(icdr_val).strip() != "" and float(icdr_val) in [0.0, 1.0, 2.0, 3.0, 4.0]

        ami_val = row.get("acute_myocardial_infarction")
        ami_binary = int(float(ami_val)) if (pd.notna(ami_val) and float(ami_val) in [0.0, 1.0]) else -1

        status = "INCLUDED"
        excl_reason = None

        if not file_exists:
            status = "EXCLUDED"
            excl_reason = "EXCL_NO_FILE: Image file referenced in metadata not present on storage disk"
        elif not vd_valid:
            status = "EXCLUDED"
            excl_reason = "EXCL_NO_LABEL: Image present on disk, but vascular_disease label is missing or NaN"

        # Record in manifest
        rel_path = f"images/{fname}" if file_exists else f"MISSING/{fname}"
        manifest_record = {
            "patient": patient_id,
            "file": fname,
            "relative_path": rel_path,
            "on_disk": file_exists,
            "vascular_disease": int(float(vd_val)) if vd_valid else -1,
            "systemic_hypertension": int(float(ht_val)) if ht_valid else -1,
            "dr_grade": int(float(icdr_val)) if icdr_valid else -1,
            "acute_myocardial_infarction": ami_binary,
            "age": row.get("age"),
            "sex": row.get("sex"),
            "laterality": row.get("laterality"),
            "final_quality": row.get("final_quality"),
            "final_artifacts": row.get("final_artifacts"),
            "status": status,
            "exclusion_reason": excl_reason,
        }
        manifest_rows.append(manifest_record)

        if status == "EXCLUDED":
            exclusion_rows.append({
                "patient": patient_id,
                "file": fname,
                "reason_code": excl_reason.split(":")[0] if excl_reason else "UNKNOWN",
                "detailed_reason": excl_reason,
                "on_disk": file_exists,
                "has_vascular_disease_label": vd_valid,
                "has_hypertension_label": ht_valid,
                "has_dr_label": icdr_valid,
            })

    df_manifest = pd.DataFrame(manifest_rows)
    df_exclusions = pd.DataFrame(exclusion_rows)

    # Save manifest and exclusions
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "dataset_manifest.csv"
    exclusions_path = output_dir / "audit_exclusions.csv"

    df_manifest.to_csv(manifest_path, index=False)
    df_exclusions.to_csv(exclusions_path, index=False)

    print(f"[PrepareData] Saved dataset manifest: {manifest_path} ({len(df_manifest)} total records)")
    print(f"[PrepareData] Saved exclusions report: {exclusions_path} ({len(df_exclusions)} excluded records)")
    print(f"[PrepareData]   - Excluded no-file: {len(df_exclusions[df_exclusions['reason_code'] == 'EXCL_NO_FILE'])}")
    print(f"[PrepareData]   - Excluded no-label: {len(df_exclusions[df_exclusions['reason_code'] == 'EXCL_NO_LABEL'])}")

    df_included = df_manifest[df_manifest["status"] == "INCLUDED"].copy()
    print(f"[PrepareData] Included eligible records: {len(df_included)} images across {df_included['patient'].nunique()} unique patients")

    return df_included, df_exclusions


def create_or_verify_splits(
    df_included: pd.DataFrame,
    existing_splits_dir: Optional[Path],
    output_splits_dir: Path,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Create or verify deterministic patient-level splits.
    If existing_splits_dir contains valid zero-leakage partitions that cover the
    included patients, we preserve the partition assignment and apply pure vascular_disease.
    Otherwise, we generate a fresh stratified partition.
    """
    output_splits_dir.mkdir(parents=True, exist_ok=True)

    can_preserve_existing = False
    if existing_splits_dir and (existing_splits_dir / "test.csv").exists():
        ex_train = pd.read_csv(existing_splits_dir / "train.csv")
        ex_val = pd.read_csv(existing_splits_dir / "val.csv")
        ex_test = pd.read_csv(existing_splits_dir / "test.csv")

        train_pts = set(ex_train["patient"].unique())
        val_pts = set(ex_val["patient"].unique())
        test_pts = set(ex_test["patient"].unique())

        # Verify zero leakage in existing
        no_leak = (len(train_pts & val_pts) == 0 and
                   len(train_pts & test_pts) == 0 and
                   len(val_pts & test_pts) == 0)

        all_split_pts = train_pts | val_pts | test_pts
        included_pts = set(df_included["patient"].unique())

        if no_leak and all_split_pts == included_pts:
            print("[PrepareData] Preserving existing benchmark patient partition boundaries (Zero Leakage confirmed).")
            can_preserve_existing = True

            # Assign split based on patient
            patient_to_split = {}
            for p in train_pts:
                patient_to_split[p] = "train"
            for p in val_pts:
                patient_to_split[p] = "val"
            for p in test_pts:
                patient_to_split[p] = "test"

            df_included["split"] = df_included["patient"].map(patient_to_split)
            train_df = df_included[df_included["split"] == "train"].copy().reset_index(drop=True)
            val_df = df_included[df_included["split"] == "val"].copy().reset_index(drop=True)
            test_df = df_included[df_included["split"] == "test"].copy().reset_index(drop=True)

    if not can_preserve_existing:
        print("[PrepareData] Generating fresh patient-level stratified split...")
        patient_df = df_included.groupby("patient").agg({
            "vascular_disease": "first",
            "systemic_hypertension": "first",
            "file": "count"
        }).rename(columns={"file": "image_count"})

        # Joint strata key for balanced multi-task distribution
        strata = (patient_df["vascular_disease"].values * 2) + (patient_df["systemic_hypertension"].values == 1).astype(int)
        patient_ids = patient_df.index.values

        temp_ratio = val_ratio + test_ratio
        sss1 = StratifiedShuffleSplit(n_splits=1, test_size=temp_ratio, random_state=seed)
        train_idx, temp_idx = next(sss1.split(patient_ids, strata))

        train_pts = set(patient_ids[train_idx])
        temp_pts = patient_ids[temp_idx]
        temp_strata = strata[temp_idx]

        relative_test_ratio = test_ratio / temp_ratio
        sss2 = StratifiedShuffleSplit(n_splits=1, test_size=relative_test_ratio, random_state=seed)
        val_sub_idx, test_sub_idx = next(sss2.split(temp_pts, temp_strata))

        val_pts = set(temp_pts[val_sub_idx])
        test_pts = set(temp_pts[test_sub_idx])

        # Assign split
        patient_to_split = {}
        for p in train_pts:
            patient_to_split[p] = "train"
        for p in val_pts:
            patient_to_split[p] = "val"
        for p in test_pts:
            patient_to_split[p] = "test"

        df_included["split"] = df_included["patient"].map(patient_to_split)
        train_df = df_included[df_included["split"] == "train"].copy().reset_index(drop=True)
        val_df = df_included[df_included["split"] == "val"].copy().reset_index(drop=True)
        test_df = df_included[df_included["split"] == "test"].copy().reset_index(drop=True)

    # Standardize output split columns (portable relative paths)
    split_cols = [
        "patient", "file", "relative_path", "split",
        "vascular_disease", "systemic_hypertension", "dr_grade",
        "acute_myocardial_infarction", "laterality", "age", "sex"
    ]

    train_df = train_df[split_cols]
    val_df = val_df[split_cols]
    test_df = test_df[split_cols]

    # Save splits
    train_df.to_csv(output_splits_dir / "train.csv", index=False)
    val_df.to_csv(output_splits_dir / "val.csv", index=False)
    test_df.to_csv(output_splits_dir / "test.csv", index=False)

    print(f"[PrepareData] Saved Train split: {output_splits_dir / 'train.csv'} ({len(train_df)} images, {train_df['patient'].nunique()} patients)")
    print(f"[PrepareData] Saved Val split:   {output_splits_dir / 'val.csv'} ({len(val_df)} images, {val_df['patient'].nunique()} patients)")
    print(f"[PrepareData] Saved Test split:  {output_splits_dir / 'test.csv'} ({len(test_df)} images, {test_df['patient'].nunique()} patients)")

    # Assertions
    tr_p = set(train_df["patient"].unique())
    va_p = set(val_df["patient"].unique())
    te_p = set(test_df["patient"].unique())

    assert len(tr_p & va_p) == 0, "Patient leakage detected between Train and Val!"
    assert len(tr_p & te_p) == 0, "Patient leakage detected between Train and Test!"
    assert len(va_p & te_p) == 0, "Patient leakage detected between Val and Test!"

    print("[PrepareData] ZERO PATIENT LEAKAGE VERIFIED across all partitions.")

    return train_df, val_df, test_df


def main():
    parser = argparse.ArgumentParser(description="CareConnect Retinal AI Data Preparation")
    parser.add_argument("--data-root", type=str, default="C:/Users/vinay/CVD Project", help="Root directory containing mBRSET")
    parser.add_argument("--output-dir", type=str, default="ml/datasets", help="Output directory for manifests and splits")
    parser.add_argument("--existing-splits", type=str, default="C:/Users/vinay/CVD Project/data/splits", help="Path to existing splits to verify/preserve")
    args = parser.parse_args()

    data_root = Path(args.data_root)
    output_dir = Path(args.output_dir)
    existing_splits_dir = Path(args.existing_splits) if args.existing_splits else None

    print("=" * 70)
    print("CARECONNECT RETINAL AI: DATA PIPELINE PREPARATION")
    print(f"Data Root:       {data_root}")
    print(f"Output Dir:      {output_dir}")
    print("=" * 70)

    csv_path, img_dir = find_mbrset_paths(data_root)
    df_included, df_exclusions = generate_manifest_and_exclusions(csv_path, img_dir, output_dir)

    splits_dir = output_dir / "splits"
    create_or_verify_splits(df_included, existing_splits_dir, splits_dir)

    print("=" * 70)
    print("DATA PIPELINE PREPARATION COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    main()
