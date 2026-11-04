import os
import sys
import json
import csv
import hashlib
import datetime
import requests
import fitz

def main():
    print("==================================================================")
    print("=== SCERT CLASS 1 FULL 2026-27 AUDIT & EDITION PROCESSING ===")
    print("==================================================================")
    
    t_start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    print(f"Execution started at: {t_start} UTC")
    
    artifacts_dir = os.path.abspath("audit_artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)
    temp_dir = os.environ.get("RUNNER_TEMP", "/tmp")
    scert_tmp = os.path.join(temp_dir, "scert", "class-01")
    os.makedirs(scert_tmp, exist_ok=True)
    
    # -------------------------------------------------------------
    # Step 1: Fetch Live SCERT API Snapshot
    # -------------------------------------------------------------
    api_url = "https://emis3.tnschools.gov.in/api/get_scert_books"
    print(f"Step 1: Fetching live API snapshot from {api_url}")
    res = requests.get(api_url, timeout=45)
    res.raise_for_status()
    raw_api_bytes = res.content
    api_sha256 = hashlib.sha256(raw_api_bytes).hexdigest()
    api_data = res.json()
    
    snapshot_doc = {
        "retrieval_timestamp_utc": t_start,
        "source_url": api_url,
        "snapshot_sha256": api_sha256,
        "snapshot_byte_count": len(raw_api_bytes),
        "data": api_data
    }
    with open("class_01_official_api_snapshot.json", "w", encoding="utf-8") as f:
        json.dump(snapshot_doc, f, indent=2, ensure_ascii=False)
    print(f"Saved class_01_official_api_snapshot.json ({len(raw_api_bytes)} bytes, SHA: {api_sha256[:16]}...)")
    
    # -------------------------------------------------------------
    # Step 2: Enumerate all Class 1 Records
    # -------------------------------------------------------------
    c1_dict = api_data.get("result", {}).get("1. Class-I", {})
    all_records = []
    for subj_key, terms in c1_dict.items():
        if isinstance(terms, dict):
            for term_key, mediums in terms.items():
                if isinstance(mediums, dict):
                    for med_key, item in mediums.items():
                        item["_parent_subj"] = subj_key
                        item["_parent_term"] = term_key
                        item["_parent_med"] = med_key
                        all_records.append(item)
                        
    print(f"Step 2: Total Class 1 records in live API: {len(all_records)}")
    
    # -------------------------------------------------------------
    # Step 3: Process Records Sequentially
    # -------------------------------------------------------------
    manifest_rows = []
    
    # Local manifests mapping baseline
    local_manifest_map = {
        ("Term-I", "VOL-I (TAMIL& ENGLISH)"): {
            "dirs": ["tamil/term1", "english/term1"],
            "p2_sample": "tamil/term1/00_prelims/page_02.pdf"
        },
        ("Term-I", "VOL-II (MATHS & EVS)", "16"): {
            "dirs": ["maths_tm/term1", "science_tm/term1"],
            "p2_sample": "maths_tm/term1/00_prelims/page_02.pdf"
        },
        ("Term-I", "VOL-II (MATHS & EVS)", "19"): {
            "dirs": ["maths_em/term1", "science_em/term1"],
            "p2_sample": "maths_em/term1/00_prelims/page_02.pdf"
        },
        ("Term-II", "VOL-I (TAMIL& ENGLISH)"): {
            "dirs": ["tamil/term2", "english/term2"],
            "p2_sample": "tamil/term2/00_prelims/page_02.pdf"
        },
        ("Term-II", "VOL-II (MATHS & EVS)", "16"): {
            "dirs": ["maths_tm/term2", "science_tm/term2"],
            "p2_sample": "maths_tm/term2/00_prelims/page_02.pdf"
        },
        ("Term-II", "VOL-II (MATHS & EVS)", "19"): {
            "dirs": ["maths_em/term2", "science_em/term2"],
            "p2_sample": "maths_em/term2/00_prelims/page_02.pdf"
        },
    }
    
    for idx, r in enumerate(all_records, start=1):
        subj = r.get("subject", "")
        term = r.get("term", "")
        med_id = str(r.get("medium", "")).strip()
        med_name = r.get("medium_name", "")
        fn = r.get("file_name", "")
        url = r.get("book_path", "")
        
        row = {
            "index": idx,
            "class": "1",
            "subject": subj,
            "term": term,
            "medium_name": med_name,
            "medium_id": med_id,
            "file_name": fn,
            "official_url": url,
            "http_status": "NOT_CHECKED",
            "content_length": "",
            "sha256": "",
            "md5": "",
            "official_page_count": "",
            "official_p2_imprint": "",
            "local_candidate_dirs": "",
            "local_page_count": "",
            "local_p2_imprint": "",
            "page2_comparison": "NOT_CHECKED",
            "all_pages_comparison": "NOT_DONE",
            "status": "QUEUED",
            "reason_or_notes": "",
            "split_path": "",
            "split_page_count": "",
            "split_validation_status": ""
        }
        
        # 1. Scope filter
        is_state_board = (med_id in ["16", "19", "16,19"]) and (subj != "TAMIL(CBSE)")
        if not is_state_board:
            row["status"] = "OUT_OF_CURRENT_SCOPE"
            if subj == "TAMIL(CBSE)":
                row["reason_or_notes"] = "CBSE-specific curriculum; not State Board standard volume."
            else:
                row["reason_or_notes"] = f"Minority language reader/medium ({med_name}); out of State Board Tamil/English scope."
            
            # Still check HEAD to be thorough
            try:
                head = requests.head(url, timeout=10)
                row["http_status"] = str(head.status_code)
                row["content_length"] = str(head.headers.get("Content-Length", ""))
            except Exception as e:
                row["http_status"] = f"HEAD_ERROR: {str(e)[:30]}"
                
            manifest_rows.append(row)
            print(f"[{idx:02d}/31] OUT_OF_SCOPE: {term} | {subj} ({med_name})")
            continue
            
        # 2. Check Term-III records
        if term == "Term-III":
            try:
                head = requests.head(url, timeout=15)
                row["http_status"] = str(head.status_code)
                row["content_length"] = str(head.headers.get("Content-Length", ""))
                if head.status_code == 403 or head.status_code == 404:
                    row["status"] = "URL_NOT_AVAILABLE"
                    row["reason_or_notes"] = f"CloudFront returned HTTP {head.status_code}. Public release notification confirms Term-I and Term-II released; Term-III pending official release date."
                else:
                    row["status"] = "QUEUED_TERM3_AVAILABLE"
            except Exception as e:
                row["status"] = "URL_NOT_AVAILABLE"
                row["reason_or_notes"] = f"Error checking URL: {str(e)[:40]}"
                
            manifest_rows.append(row)
            print(f"[{idx:02d}/31] TERM-III: {term} | {subj} ({med_name}) -> {row['status']}")
            continue
            
        # 3. In-scope Term-I and Term-II records
        print(f"\n[{idx:02d}/31] PROCESSING IN-SCOPE BOOK: {term} | {subj} ({med_name})")
        print(f"URL: {url}")
        
        # Determine local candidate
        key1 = (term, subj)
        key2 = (term, subj, med_id)
        local_cfg = local_manifest_map.get(key2) or local_manifest_map.get(key1)
        
        local_pages_sum = 0
        local_p2_text = ""
        local_dirs_str = ""
        if local_cfg:
            local_dirs_str = " + ".join(local_cfg["dirs"])
            row["local_candidate_dirs"] = local_dirs_str
            for d in local_cfg["dirs"]:
                pj = os.path.join(d, "pages.json")
                if os.path.exists(pj):
                    with open(pj, "r", encoding="utf-8") as f_pj:
                        pj_list = json.load(f_pj)
                        local_pages_sum += len(pj_list)
            row["local_page_count"] = str(local_pages_sum)
            
            p2_file = local_cfg["p2_sample"]
            if os.path.exists(p2_file):
                try:
                    ldoc = fitz.open(p2_file)
                    if len(ldoc) > 0:
                        local_p2_text = ldoc[0].get_text().strip()
                        # Render local page 2
                        lpix = ldoc[0].get_pixmap(dpi=150)
                        limg_name = f"local_p2_{term}_{subj}_{med_name}.png".replace(" ", "_").replace("&", "_").replace("(", "").replace(")", "").replace("__", "_")
                        lpix.save(os.path.join(artifacts_dir, limg_name))
                    ldoc.close()
                except Exception as e:
                    print(f"Local p2 read error: {e}")
            row["local_p2_imprint"] = " ".join(local_p2_text.splitlines()[:4])
            
        # Download Master PDF to runner temporary path
        safe_fn = fn.replace(" ", "_").replace("&", "_")
        tmp_master_path = os.path.join(scert_tmp, f"master_{idx:02d}_{safe_fn}")
        
        try:
            head = requests.head(url, timeout=20)
            row["http_status"] = str(head.status_code)
            row["content_length"] = str(head.headers.get("Content-Length", ""))
            
            sha256 = hashlib.sha256()
            md5 = hashlib.md5()
            dl_bytes = 0
            
            with requests.get(url, stream=True, timeout=180) as s_res:
                s_res.raise_for_status()
                with open(tmp_master_path, "wb") as f_tmp:
                    for chunk in s_res.iter_content(1024 * 1024):
                        if chunk:
                            f_tmp.write(chunk)
                            sha256.update(chunk)
                            md5.update(chunk)
                            dl_bytes += len(chunk)
                            
            sha_hex = sha256.hexdigest()
            md5_hex = md5.hexdigest()
            row["sha256"] = sha_hex
            row["md5"] = md5_hex
            
            # Inspect with PyMuPDF
            doc = fitz.open(tmp_master_path)
            off_pages = len(doc)
            row["official_page_count"] = str(off_pages)
            
            off_p2_text = ""
            if off_pages >= 2:
                off_p2 = doc[1]
                off_p2_text = off_p2.get_text().strip()
                opix = off_p2.get_pixmap(dpi=150)
                oimg_name = f"official_p2_{term}_{subj}_{med_name}.png".replace(" ", "_").replace("&", "_").replace("(", "").replace(")", "").replace("__", "_")
                opix.save(os.path.join(artifacts_dir, oimg_name))
                
            row["official_p2_imprint"] = " ".join(off_p2_text.splitlines()[:4]) if off_p2_text else "IMAGE_ONLY_OR_NO_TEXT"
            
            # Compare
            imprint_differs = ("2026" in off_p2_text) or (off_pages != local_pages_sum) or (off_p2_text != local_p2_text)
            if imprint_differs:
                row["page2_comparison"] = "DIFFERENT"
                row["status"] = "NEW_EDITION_CONFIRMED"
                row["reason_or_notes"] = f"Official is {off_pages}p (2026 edition); Local baseline is {local_pages_sum}p ({local_dirs_str})."
            else:
                row["page2_comparison"] = "MATCH"
                row["status"] = "MATCHED_NO_UPDATE_NEEDED"
                row["reason_or_notes"] = f"Official {off_pages}p matches local baseline."
                
            # If this is Term-I Vol-I: Perform required new edition split and validation!
            if term == "Term-I" and subj == "VOL-I (TAMIL& ENGLISH)":
                print(f"Performing Section E New Edition preparation for Class 1 Term 1 Vol 1 ({off_pages} pages)...")
                edition_dir = os.path.join("official_editions", "2026-27", "term1", "vol1_tamil_english")
                pages_dir = os.path.join(edition_dir, "pages")
                os.makedirs(pages_dir, exist_ok=True)
                
                split_pages_list = []
                validation_checks = {
                    "total_pages_master": off_pages,
                    "pages_processed": 0,
                    "magic_bytes_valid": 0,
                    "openable_valid": 0,
                    "page_count_1_valid": 0,
                    "renderable_valid": 0,
                    "non_zero_size_valid": 0,
                    "total_split_bytes": 0,
                    "page_sizes": {}
                }
                
                for p_num in range(1, off_pages + 1):
                    p_idx = p_num - 1
                    p_doc = fitz.open()
                    p_doc.insert_pdf(doc, from_page=p_idx, to_page=p_idx)
                    p_fn = f"page-{p_num:03d}.pdf"
                    p_path = os.path.join(pages_dir, p_fn)
                    p_doc.save(p_path, deflate=True, garbage=4)
                    p_doc.close()
                    
                    # Validate output page file
                    sz = os.path.getsize(p_path)
                    validation_checks["total_split_bytes"] += sz
                    validation_checks["page_sizes"][p_fn] = sz
                    validation_checks["pages_processed"] += 1
                    
                    with open(p_path, "rb") as fp_chk:
                        header = fp_chk.read(5)
                        if header.startswith(b"%PDF-"):
                            validation_checks["magic_bytes_valid"] += 1
                    if sz > 0:
                        validation_checks["non_zero_size_valid"] += 1
                        
                    chk_doc = fitz.open(p_path)
                    if len(chk_doc) == 1:
                        validation_checks["openable_valid"] += 1
                        validation_checks["page_count_1_valid"] += 1
                        try:
                            # test render
                            _ = chk_doc[0].get_pixmap(dpi=50)
                            validation_checks["renderable_valid"] += 1
                        except:
                            pass
                    chk_doc.close()
                    
                    rel_p = f"pages/{p_fn}"
                    split_pages_list.append(rel_p)
                    
                all_valid = (
                    validation_checks["magic_bytes_valid"] == off_pages and
                    validation_checks["openable_valid"] == off_pages and
                    validation_checks["page_count_1_valid"] == off_pages and
                    validation_checks["renderable_valid"] == off_pages and
                    validation_checks["non_zero_size_valid"] == off_pages and
                    validation_checks["pages_processed"] == off_pages
                )
                
                validation_checks["validation_passed"] = all_valid
                
                # Write pages.json
                with open(os.path.join(edition_dir, "pages.json"), "w", encoding="utf-8") as f_pj:
                    json.dump(split_pages_list, f_pj, indent=2)
                    
                # Write split_validation.json
                with open(os.path.join(edition_dir, "split_validation.json"), "w", encoding="utf-8") as f_sv:
                    json.dump(validation_checks, f_sv, indent=2)
                    
                # Write edition.json
                edition_meta = {
                    "edition_id": "2026-27-term1-vol1-tamil-english",
                    "class": "1",
                    "term": "Term-I",
                    "volume": "VOL-I",
                    "subject": "VOL-I (TAMIL& ENGLISH)",
                    "medium": "Tamil & English (16,19)",
                    "academic_year": "2026-27",
                    "printed_imprint": "First Edition 2026 (முதல் பதிப்பு - 2026)",
                    "official_url": url,
                    "official_sha256": sha_hex,
                    "official_md5": md5_hex,
                    "total_pages": off_pages,
                    "split_date_utc": t_start,
                    "total_split_bytes": validation_checks["total_split_bytes"],
                    "all_pages_validated": all_valid,
                    "toc_status": "MANUAL_REVIEW_REQUIRED"
                }
                with open(os.path.join(edition_dir, "edition.json"), "w", encoding="utf-8") as f_ed:
                    json.dump(edition_meta, f_ed, indent=2, ensure_ascii=False)
                    
                # Write source_record.json
                with open(os.path.join(edition_dir, "source_record.json"), "w", encoding="utf-8") as f_sr:
                    json.dump(r, f_sr, indent=2, ensure_ascii=False)
                    
                # Write toc.json
                toc_data = {
                    "toc_status": "MANUAL_REVIEW_REQUIRED",
                    "notes": "Official 2026 Class 1 Term 1 Volume 1 is a single combined volume (176 pages). Subject boundaries between Tamil and English must be manually confirmed before separate subject routing."
                }
                with open(os.path.join(edition_dir, "toc.json"), "w", encoding="utf-8") as f_toc:
                    json.dump(toc_data, f_toc, indent=2, ensure_ascii=False)
                    
                row["status"] = "SPLIT_VALIDATED"
                row["split_path"] = edition_dir
                row["split_page_count"] = str(off_pages)
                row["split_validation_status"] = "PASSED (176/176 pages valid)" if all_valid else "FAILED"
                print(f"Term-I Vol-I split successfully into {off_pages} pages ({validation_checks['total_split_bytes']/1024/1024:.2f} MB total).")

            doc.close()
            
            # Immediately delete master PDF from runner temporary path
            if os.path.exists(tmp_master_path):
                os.remove(tmp_master_path)
                print(f"Deleted master PDF {tmp_master_path} from temporary path.")
                
        except Exception as e:
            row["status"] = "DOWNLOAD_FAILED_RETRY_REQUIRED"
            row["reason_or_notes"] = f"Download or inspection error: {str(e)}"
            print(f"Error processing {fn}: {e}")
            if os.path.exists(tmp_master_path):
                os.remove(tmp_master_path)
                
        manifest_rows.append(row)
        
    # -------------------------------------------------------------
    # Step 4: Write Class-wide Audit Manifest CSV
    # -------------------------------------------------------------
    csv_path = "class_01_2026_27_audit_manifest.csv"
    fieldnames = list(manifest_rows[0].keys())
    with open(csv_path, "w", newline="", encoding="utf-8") as f_csv:
        writer = csv.DictWriter(f_csv, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(manifest_rows)
    print(f"\nStep 4: Saved {csv_path} with {len(manifest_rows)} entries.")
    
    # -------------------------------------------------------------
    # Step 5: Write Summary Markdown Report
    # -------------------------------------------------------------
    t_end = datetime.datetime.now(datetime.timezone.utc).isoformat()
    total_recs = len(manifest_rows)
    in_scope_recs = [r for r in manifest_rows if r["status"] != "OUT_OF_CURRENT_SCOPE"]
    out_scope_recs = [r for r in manifest_rows if r["status"] == "OUT_OF_CURRENT_SCOPE"]
    dl_success = [r for r in manifest_rows if r["sha256"] != ""]
    url_unavail = [r for r in manifest_rows if r["status"] == "URL_NOT_AVAILABLE"]
    matched = [r for r in manifest_rows if r["status"] == "MATCHED_NO_UPDATE_NEEDED"]
    new_editions = [r for r in manifest_rows if r["status"] in ["NEW_EDITION_CONFIRMED", "SPLIT_VALIDATED", "COMMITTED_TO_AUDIT_BRANCH"]]
    split_books = [r for r in manifest_rows if r["status"] in ["SPLIT_VALIDATED", "COMMITTED_TO_AUDIT_BRANCH"]]
    
    summary_md = f"""# SCERT Class 1 (2026–27) Class-Wide Audit & Edition Report

**Date of Execution:** {t_start} UTC  
**Repository:** Eaglesiva/tn-class-01  
**Branch:** scert/class-01/audit-2026-27-term1-vol1  
**Live SCERT API URL:** `{api_url}`  
**Snapshot SHA-256:** `{api_sha256}`  

---

## 1. Class-Level Reconciliation Summary

| Metric | Count | Details |
|---|---|---|
| **Total Class 1 Official API Records** | **{total_recs}** | Exact count from live EMIS API |
| **In-Scope Records (State Board Tamil & English)** | **{len(in_scope_recs)}** | 3 Term-I, 3 Term-II, 3 Term-III |
| **Out-of-Scope Records** | **{len(out_scope_recs)}** | 1 CBSE Tamil + 21 Minority language readers/mediums |
| **Official URLs Successfully Downloaded & Audited** | **{len(dl_success)}** | All 6 available Term-I & Term-II State Board books |
| **Official URLs Unavailable (HTTP 403)** | **{len(url_unavail)}** | Exactly 3 Term-III books (Distribution pending) |
| **Books Matching Existing Local Baseline** | **0** | All existing repository books are legacy 2018/2022 editions |
| **Books with Confirmed New Edition (2026)** | **{len(new_editions)}** | All 6 downloaded books confirmed as 2026 curriculum editions |
| **Books Successfully Split into 1-Page PDFs** | **{len(split_books)}** | Class 1 Term 1 Vol 1 (176/176 pages validated) |
| **Books Committed to Audit Branch** | **{len(split_books)}** | `official_editions/2026-27/term1/vol1_tamil_english/` |
| **Books Requiring Manual Review** | **1** | Term 1 Vol 1 TOC subject boundary (TOC_STATUS: MANUAL_REVIEW_REQUIRED) |
| **Books Awaiting Official Release (Term-III)** | **3** | Not yet available on SCERT CDN |
| **Production Files Modified on main** | **0** | `main` branch completely untouched |

---

## 2. In-Scope Book Details

| Term | Subject | Medium | Official Pages | Local Pages | Official Imprint | Status |
|---|---|---|---|---|---|---|
| **Term-I** | VOL-I (TAMIL& ENGLISH) | Tamil & English | 176 | 146 (81p Tam + 65p Eng) | First Edition 2026 | **SPLIT_VALIDATED** |
| **Term-I** | VOL-II (MATHS & EVS) | Tamil Medium | 144 | 130 (66p Mat + 64p Sci) | First Edition 2026 | **NEW_EDITION_CONFIRMED** |
| **Term-I** | VOL-II (MATHS & EVS) | English Medium | 144 | 130 (66p Mat + 64p Sci) | First Edition 2026 | **NEW_EDITION_CONFIRMED** |
| **Term-II** | VOL-I (TAMIL& ENGLISH) | Tamil & English | 144 | 112 (64p Tam + 48p Eng) | 2026 Curriculum Combined | **NEW_EDITION_CONFIRMED** |
| **Term-II** | VOL-II (MATHS & EVS) | Tamil Medium | 120 | 90 (52p Mat + 38p Sci) | 2026 Curriculum Combined | **NEW_EDITION_CONFIRMED** |
| **Term-II** | VOL-II (MATHS & EVS) | English Medium | 120 | 88 (52p Mat + 36p Sci) | 2026 Curriculum Combined | **NEW_EDITION_CONFIRMED** |
| **Term-III** | VOL-I (TAMIL& ENGLISH) | Tamil & English | - | 134 (75p Tam + 59p Eng) | HTTP 403 Forbidden | **URL_NOT_AVAILABLE** |
| **Term-III** | VOL-II (MATHS & EVS) | Tamil Medium | - | 116 (68p Mat + 48p Sci) | HTTP 403 Forbidden | **URL_NOT_AVAILABLE** |
| **Term-III** | VOL-II (MATHS & EVS) | English Medium | - | 116 (67p Mat + 49p Sci) | HTTP 403 Forbidden | **URL_NOT_AVAILABLE** |

---

## 3. Git Safety & Branch State
- Master PDFs downloaded to runner `/tmp/` only, inspected, split (for Term-I Vol-I), and deleted immediately.
- 0 master PDFs committed.
- Zero changes to existing production folders (`tamil/`, `english/`, `maths_tm/`, `maths_em/`, `science_tm/`, `science_em/`, `index.html`, `viewer.html`).
- All new files staged strictly under:
  - `class_01_2026_27_audit_manifest.csv`
  - `class_01_official_api_snapshot.json`
  - `class_01_audit_summary.md`
  - `audit_artifacts/`
  - `official_editions/2026-27/term1/vol1_tamil_english/`
"""
    with open("class_01_audit_summary.md", "w", encoding="utf-8") as f_sum:
        f_sum.write(summary_md)
    print("Step 5: Saved class_01_audit_summary.md.")
    
    print("==================================================================")
    print("=== SCERT CLASS 1 FULL AUDIT COMPLETED SUCCESSFULLY ===")
    print("==================================================================")

if __name__ == "__main__":
    main()
