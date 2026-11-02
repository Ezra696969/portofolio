import json
import os

research_projects = [
    {
        "id": "idx-financial-extraction",
        "category": "fin",
        "category_label": "Financial AI",
        "title": "Automated Financial Statement Intelligence for IDX",
        "subtitle": "Layout-Aware Table Parsing and Double-Entry Accounting Reconciliation",
        "author": "Greg Ezra",
        "affiliation": "Teknologi Sains Data, Universitas Airlangga",
        "period": "2026",
        "status_badge": "Verified Whitepaper",
        "lead": "Mengeliminasi halusinasi model AI pada ekstraksi laporan keuangan emiten Bursa Efek Indonesia melalui verifikasi persamaan akuntansi formal PSAK 1 / IFRS.",
        "metrics": [
            ["Cell Exact Match", "100.0%"],
            ["Accounting Identity Pass", "100.0%"],
            ["Toleransi Error", "<= 0.05%"],
            ["Halusinasi Numerik", "0.0% (Rejected)"]
        ],
        "sources": [
            "Laporan Keuangan Tahunan Resmi Audited Emiten IDX (idx.co.id)",
            "Standar Akuntansi Keuangan: PSAK 1 Penyajian Laporan Keuangan (IAI)",
            "PubTables-1M & Table Transformer (CVPR)"
        ],
        "tags": ["Financial NLP", "Document AI", "PSAK 1", "Accounting Identities", "Python"],
        "paper_file": r"E:\Project\RESEARCH\01-idx-financial-statement-ocr\PAPER.md",
        "repo_folder": "RESEARCH/01-idx-financial-statement-ocr"
    },
    {
        "id": "lkpp-procurement-anomaly",
        "category": "gov",
        "category_label": "Public Forensics",
        "title": "Algorithmic Detection of Bid Rigging in Public Procurement",
        "subtitle": "Forensic Digit Analysis (Benford's Law) and Bipartite Network Graph Centrality",
        "author": "Greg Ezra",
        "affiliation": "Teknologi Sains Data, Universitas Airlangga",
        "period": "2026",
        "status_badge": "Verified Whitepaper",
        "lead": "Sistem peringatan dini deteksi kartel tender, sindikat penawar pendamping (cover bidding), dan anomali nilai lelang pengadaan pemerintah LKPP/LPSE.",
        "metrics": [
            ["Uji Benford (MAD)", "0.0078 vs 0.0241"],
            ["Deteksi Klik Kartel", "High Precision"],
            ["Threshold Penawaran HPS", ">= 99.5% Flagged"],
            ["Standar Audit", "OECD & World Bank"]
        ],
        "sources": [
            "Data Terbuka LKPP / LPSE / INAPROC (Perpres 12/2021)",
            "World Bank Integrity Vice Presidency (INT) Procurement Red Flags",
            "OECD Guidelines for Fighting Bid Rigging in Public Procurement",
            "Standar Audit Forensik Benford's Law (Mark J. Nigrini)"
        ],
        "tags": ["Forensic Data Science", "Benford's Law", "Graph Theory", "Public Procurement", "LKPP"],
        "paper_file": r"E:\Project\RESEARCH\02-lkpp-procurement-anomaly\PAPER.md",
        "repo_folder": "RESEARCH/02-lkpp-procurement-anomaly"
    },
    {
        "id": "geospatial-deforestation-sentinel",
        "category": "geo",
        "category_label": "Geospatial & Climate",
        "title": "Tropical Deforestation & Wildfire Damage Assessment",
        "subtitle": "Multi-Temporal Sentinel-2 Multispectral Indices and Deep U-Net Architecture",
        "author": "Greg Ezra",
        "affiliation": "Teknologi Sains Data, Universitas Airlangga",
        "period": "2026",
        "status_badge": "Verified Whitepaper",
        "lead": "Kombinasi indeks biofisik analitik (dNBR, NDVI) dan deep learning U-Net untuk pemetaan resolusi tinggi (10m) kerusakan hutan tropis dan kebakaran gambut di Indonesia.",
        "metrics": [
            ["IoU (Jaccard)", "0.862"],
            ["Dice Coefficient (F1)", "0.925"],
            ["Resolusi Spasial", "10 meter / piksel"],
            ["Precision", "0.931"]
        ],
        "sources": [
            "European Space Agency (ESA) Copernicus Sentinel-2 Level-2A (10m)",
            "USGS Burn Severity Standard & European Forest Fire Info System (EFFIS)",
            "NASA FIRMS MODIS/VIIRS Active Fire Data",
            "Kementerian Lingkungan Hidup dan Kehutanan (SIPONGI KLHK)"
        ],
        "tags": ["Remote Sensing", "Sentinel-2", "dNBR", "PyTorch U-Net", "Peatland Wildfire"],
        "paper_file": r"E:\Project\RESEARCH\03-geospatial-deforestation-sentinel\PAPER.md",
        "repo_folder": "RESEARCH/03-geospatial-deforestation-sentinel"
    }
]

for p in research_projects:
    if os.path.exists(p["paper_file"]):
        with open(p["paper_file"], "r", encoding="utf-8") as f:
            p["paper_content"] = f.read()
    else:
        p["paper_content"] = ""

out_json = r"E:\Project\PORTFOLIO\site\research\research_data.json"
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(research_projects, f, ensure_ascii=False, indent=2)

print(f"Generated {out_json} successfully with {len(research_projects)} research projects.")
