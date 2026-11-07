#!/usr/bin/env python3
"""Read existing Class 1 split PDFs and extract Page 2 + TOC evidence."""
import argparse
import json
from pathlib import Path
import fitz

BOOKS = [
    ("term1-vol1-tamil-english", "official_editions/2026-27/term1/vol1_tamil_english", "Term-I · VOL-I (TAMIL & ENGLISH)"),
    ("term1-vol2-maths-evs-tm", "official_editions/2026-27/term1/vol2_maths_evs_tm", "Term-I · VOL-II (MATHS & EVS) · Tamil"),
    ("term1-vol2-maths-evs-em", "official_editions/2026-27/term1/vol2_maths_evs_em", "Term-I · VOL-II (MATHS & EVS) · English"),
    ("term2-vol1-tamil-english", "official_editions/2026-27/term2/vol1_tamil_english", "Term-II · VOL-I (TAMIL & ENGLISH)"),
    ("term2-vol2-maths-evs-tm", "official_editions/2026-27/term2/vol2_maths_evs_tm", "Term-II · VOL-II (MATHS & EVS) · Tamil"),
    ("term2-vol2-maths-evs-em", "official_editions/2026-27/term2/vol2_maths_evs_em", "Term-II · VOL-II (MATHS & EVS) · English"),
]
TOC_TERMS = ["பொருளடக்கம்", "பொருளடக்க", "உள்ளடக்கம்", "contents", "table of contents"]

def clean_text(text):
    text = (text or "").replace("\x00", "")
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()

def get_single_page_text(path):
    with fitz.open(path) as doc:
        if len(doc) < 1:
            return "", 0
        return clean_text(doc[0].get_text("text")), len(doc)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = Path(args.source).resolve()
    output = Path(args.output).resolve()
    text_dir = output / "extracted-text"
    text_dir.mkdir(parents=True, exist_ok=True)

    results = []
    md = [
        "# Class 01 — Page 2 and TOC Text Extraction",
        "",
        "**Source branch:** scert/class-01/audit-2026-27-term1-vol1",
        "**Method:** PyMuPDF extraction from existing page-split PDFs.",
        "**Scope:** Read-only. No source PDF, page manifest, production file, or viewer file changed.",
        "",
        "Text extraction is not visual proof. Empty or garbled text remains marked for manual review.",
        "",
    ]

    for slug, rel_dir, label in BOOKS:
        folder = source / rel_dir
        page_list = json.loads((folder / "pages.json").read_text(encoding="utf-8"))
        edition = json.loads((folder / "edition.json").read_text(encoding="utf-8"))
        page2_rel = next((p for p in page_list if Path(p).name == "page-002.pdf"), None)
        if not page2_rel:
            raise RuntimeError(f"Page 2 not listed for {label}")
        page2_path = folder / page2_rel
        if not page2_path.exists():
            raise FileNotFoundError(str(page2_path))
        page2_text, page2_count = get_single_page_text(page2_path)

        toc_candidates = []
        first_pages = []
        missing = []
        invalid = []
        for number, rel_page in enumerate(page_list, start=1):
            pdf_path = folder / rel_page
            if not pdf_path.exists():
                missing.append(rel_page)
                continue
            try:
                page_text, page_count = get_single_page_text(pdf_path)
                if page_count != 1:
                    invalid.append({"path": rel_page, "pdf_page_count": page_count})
                if number <= 30:
                    first_pages.append({"book_page": number, "path": rel_page, "text": page_text})
                lowered = page_text.casefold()
                hits = [term for term in TOC_TERMS if term.casefold() in lowered]
                if hits:
                    toc_candidates.append({
                        "book_page": number,
                        "path": rel_page,
                        "matched_terms": hits,
                        "text": page_text,
                    })
            except Exception as exc:
                invalid.append({"path": rel_page, "error": str(exc)})

        extracted = [
            f"# {label}",
            "",
            f"Book folder: {rel_dir}",
            f"Page 2 file: {rel_dir}/{page2_rel}",
            "",
            "## Page 2 extracted text",
            page2_text or "[NO SELECTABLE TEXT — visual review required]",
            "",
            "## TOC keyword matches",
        ]
        if toc_candidates:
            for candidate in toc_candidates:
                extracted.extend([
                    "",
                    f"### Printed PDF page {candidate['book_page']} ({candidate['path']})",
                    "Matched terms: " + ", ".join(candidate["matched_terms"]),
                    candidate["text"] or "[NO SELECTABLE TEXT]",
                ])
        else:
            extracted.extend(["", "[No explicit TOC keyword found. See first 30 pages below.]"])
        extracted.extend(["", "## First 30 pages"])
        for item in first_pages:
            extracted.extend([
                "",
                f"### Printed PDF page {item['book_page']} ({item['path']})",
                item["text"] or "[NO SELECTABLE TEXT]",
            ])
        text_file = text_dir / f"{slug}.txt"
        text_file.write_text("\n".join(extracted) + "\n", encoding="utf-8")

        result = {
            "slug": slug,
            "label": label,
            "book_path": rel_dir,
            "page_count_from_manifest": len(page_list),
            "page2_path": f"{rel_dir}/{page2_rel}",
            "page2_pdf_page_count": page2_count,
            "page2_text": page2_text,
            "page2_text_status": "EXTRACTED" if page2_text else "IMAGE_ONLY_OR_NO_TEXT",
            "toc_candidate_pages": toc_candidates,
            "toc_status": "KEYWORD_CANDIDATES_FOUND" if toc_candidates else "NO_KEYWORD_MATCH_FIRST_30_PAGES_EXPORTED",
            "missing_page_files": missing,
            "invalid_page_files": invalid,
            "edition_json": edition,
            "extracted_text_file": str(text_file.relative_to(output)),
        }
        results.append(result)

        md.extend([
            f"## {label}",
            "",
            f"- Book folder: {rel_dir}",
            f"- Manifest pages: **{len(page_list)}**",
            f"- Page 2 PDF: {rel_dir}/{page2_rel}",
            f"- Page 2 file page count: {page2_count}",
            f"- Page 2 text status: **{result['page2_text_status']}**",
            f"- Existing edition metadata imprint: {edition.get('printed_imprint', 'UNKNOWN')}",
            f"- TOC candidate pages: {', '.join(str(x['book_page']) for x in toc_candidates) if toc_candidates else 'No explicit keyword match'}",
            f"- Missing page files: {len(missing)}",
            f"- Invalid split files: {len(invalid)}",
            f"- Full extracted text: {text_file.relative_to(output)}",
            "",
            "### Page 2 extracted text",
            "",
            page2_text or "[NO SELECTABLE TEXT — visual review required]",
            "",
            "### TOC candidate text",
            "",
        ])
        if toc_candidates:
            for candidate in toc_candidates:
                md.extend([
                    f"**Printed PDF page {candidate['book_page']}** — " + ", ".join(candidate["matched_terms"]),
                    "",
                    candidate["text"] or "[NO SELECTABLE TEXT]",
                    "",
                ])
        else:
            md.extend(["No explicit TOC keyword found. See the companion TXT file for first-30-page text.", ""])

    report_json = output / "class_01_page2_toc_extraction.json"
    report_md = output / "class_01_page2_toc_extraction.md"
    report_json.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"BOOKS_PROCESSED={len(results)}")
    print(f"PAGE2_SINGLE_PAGE_FILES={sum(1 for x in results if x['page2_pdf_page_count'] == 1)}")
    print(f"TOTAL_MANIFEST_PAGES={sum(x['page_count_from_manifest'] for x in results)}")
    print(f"MISSING_PAGE_FILES={sum(len(x['missing_page_files']) for x in results)}")
    print(f"INVALID_SPLIT_FILES={sum(len(x['invalid_page_files']) for x in results)}")
    for item in results:
        print(f"{item['slug']}: PAGE2={item['page2_text_status']}; TOC={item['toc_status']}; PAGES={[x['book_page'] for x in item['toc_candidate_pages']]}")
    print(f"REPORT_MD={report_md}")
    print(f"REPORT_JSON={report_json}")

if __name__ == "__main__":
    main()
