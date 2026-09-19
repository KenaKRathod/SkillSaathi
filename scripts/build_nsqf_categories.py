"""Download NSDC Job Role List and build nsqf_categories.csv.

Usage:
    python scripts/build_nsqf_categories.py

Outputs:
    data/nsqf_categories.csv

Fallback behaviour:
    - If the download URL is unreachable or the file structure has changed,
      the script logs a clear error naming the exact URL and expected
      columns, then exits non-zero.
    - If fewer than 15 distinct sectors are found after grouping, prints a
      warning (the grouping logic likely needs manual adjustment).
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import httpx
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SOURCE_URL = (
    "https://rplrfp.nsdcindia.org/Downloads/NSDCDocument/Job_Role_List.xlsx"
)

EXPECTED_COLUMNS = {"Sector", "QP/Job Role Name", "NSQF Level"}

# Mapping from raw Sector name (after strip) → broader category.
# Keys are the 36 unique sector names found in the source data.
SECTOR_TO_CATEGORY: dict[str, str] = {
    # Agriculture
    "Agriculture": "Agriculture & Farming",
    # Textiles & Tailoring
    "Textile Sector Skill Council": "Textiles & Tailoring",
    "Apparel, Made-Ups & Home Furnishing": "Textiles & Tailoring",
    # Rubber, Chemicals & Plastics
    "RCPSDC": "Rubber, Chemicals & Plastics",
    # Electronics
    "Electronics": "Electronics & Hardware",
    # Infrastructure & Heavy Equipment
    "Infrastructure Equipment": "Infrastructure & Heavy Equipment",
    # Media & Entertainment
    "Media & Entertainment": "Media & Entertainment",
    # Logistics
    "Logistics": "Logistics & Warehousing",
    # Construction
    "Construction": "Construction & Real Estate",
    # Beauty & Wellness
    "Beauty & Wellness": "Beauty & Wellness",
    # Food Processing
    "Food Processing": "Food Processing & Packaging",
    # Handicrafts
    "Handicrafts and Carpet": "Handicrafts & Artisan Work",
    # Gems & Jewellery
    "Gem and Jewellery": "Gems & Jewellery",
    # Mining
    "Skill Council for Mining Sector": "Mining & Geology",
    # Telecom
    "Telecom": "Telecom & Networking",
    # Iron & Steel
    "Iron & Steel": "Iron, Steel & Metals",
    # IT
    "IT-ITeS": "IT & Digital Services",
    # Automotive
    "Automotive": "Automotive & Vehicle Servicing",
    # Manufacturing & Welding
    "Capital Goods Skill Council": "Manufacturing & Welding",
    # Healthcare + Life Sciences
    "Healthcare": "Healthcare & Life Sciences",
    "Life Sciences": "Healthcare & Life Sciences",
    # Oil, Gas & Energy
    "Hydrocarbon": "Oil, Gas & Energy",
    "Power": "Oil, Gas & Energy",
    # Instrumentation
    "Instrumentation Automation Surveillance and Communication SSC": (
        "Instrumentation & Automation"
    ),
    # Office & Business Support
    "Management": "Office & Business Support",
    "BFSI": "Office & Business Support",
    # Leather
    "Leather": "Leather & Footwear",
    # Tourism & Hospitality (handles the two spelling variants)
    "Tourism and Hospitality Skill Council": "Tourism & Hospitality",
    "Tourism and Hospitality SKill Council": "Tourism & Hospitality",
    # Catch-all: Retail, Sports & General Services
    "Retail": "Retail, Sports & General Services",
    "Sports": "Retail, Sports & General Services",
    "Furniture and Fittings": "Retail, Sports & General Services",
    "Plumbing": "Retail, Sports & General Services",
    "Persons with Disability": "Retail, Sports & General Services",
    "Aerospace and Aviation": "Retail, Sports & General Services",
    "Green Jobs": "Retail, Sports & General Services",
}

CATEGORY_DESCRIPTIONS: dict[str, str] = {
    "Agriculture & Farming": (
        "Crop cultivation, floriculture, landscaping, irrigation, and farm equipment operation."
    ),
    "Textiles & Tailoring": (
        "Textile manufacturing, weaving, spinning, sewing, embroidery, and apparel production."
    ),
    "Rubber, Chemicals & Plastics": (
        "Rubber processing, plastic moulding, chemical handling, and polymer manufacturing."
    ),
    "Electronics & Hardware": (
        "Electronic assembly, PCB manufacturing, mobile repair, and consumer electronics servicing."
    ),
    "Infrastructure & Heavy Equipment": (
        "Crane operation, excavation, earthmoving, and heavy machinery operation."
    ),
    "Media & Entertainment": (
        "Film production, animation, sound engineering, camera operation, and content creation."
    ),
    "Logistics & Warehousing": (
        "Warehouse management, freight handling, courier services, and supply chain operations."
    ),
    "Construction & Real Estate": (
        "Masonry, bar bending, scaffolding, painting, tiling, and building construction."
    ),
    "Beauty & Wellness": (
        "Hair styling, skin care, makeup artistry, spa therapy, and personal grooming."
    ),
    "Food Processing & Packaging": (
        "Food manufacturing, baking, dairy processing, quality testing, and packaging."
    ),
    "Handicrafts & Artisan Work": (
        "Hand weaving, pottery, carpet making, traditional craft production, and restoration."
    ),
    "Gems & Jewellery": (
        "Jewellery design, gem cutting, polishing, setting, and precious metal work."
    ),
    "Mining & Geology": (
        "Mining operations, drilling, blasting, surveying, and mineral extraction."
    ),
    "Telecom & Networking": (
        "Telecom tower installation, fibre optics, broadband servicing, and network maintenance."
    ),
    "Iron, Steel & Metals": (
        "Steel production, metal casting, forging, rolling, and metallurgical operations."
    ),
    "IT & Digital Services": (
        "Software development, data entry, BPO services, digital marketing, and IT support."
    ),
    "Automotive & Vehicle Servicing": (
        "Vehicle repair, auto body work, engine servicing, and automobile manufacturing."
    ),
    "Manufacturing & Welding": (
        "CNC machining, welding, fabrication, mechanical assembly, and industrial drafting."
    ),
    "Healthcare & Life Sciences": (
        "Nursing assistance, pharmacy operations, medical device handling, and patient care."
    ),
    "Oil, Gas & Energy": (
        "Oil drilling, refinery operations, power generation, solar installation, and gas distribution."
    ),
    "Instrumentation & Automation": (
        "Industrial automation, PLC programming, instrumentation calibration, and process control."
    ),
    "Office & Business Support": (
        "Office administration, reception, data management, security, and financial services."
    ),
    "Leather & Footwear": (
        "Leather tanning, footwear manufacturing, stitching, and leather goods production."
    ),
    "Tourism & Hospitality": (
        "Hotel operations, cooking, housekeeping, tour guiding, and travel services."
    ),
    "Retail, Sports & General Services": (
        "Retail sales, fitness training, plumbing, furniture making, waste management, "
        "and general services."
    ),
}

# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------


def download_xlsx(url: str, dest: Path) -> Path:
    """Download the xlsx file from *url* to *dest*.

    Raises ``SystemExit(1)`` with a clear diagnostic message on failure.
    """
    logger.info("Downloading %s …", url)
    try:
        with httpx.Client(follow_redirects=True, timeout=60) as client:
            response = client.get(url)
            response.raise_for_status()
    except (httpx.HTTPError, httpx.StreamError) as exc:
        logger.error(
            "FATAL — failed to download the NSDC Job Role List.\n"
            "  URL : %s\n"
            "  Error: %s\n"
            "Cannot proceed without this file. Please verify the URL is "
            "reachable and retry.",
            url,
            exc,
        )
        sys.exit(1)

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(response.content)
    logger.info("Saved %d bytes → %s", len(response.content), dest)
    return dest


def load_and_validate(path: Path) -> pd.DataFrame:
    """Read the xlsx and validate that expected columns are present.

    Raises ``SystemExit(1)`` if the file structure does not match
    expectations (columns renamed or missing).
    """
    logger.info("Loading %s …", path)
    df = pd.read_excel(path)

    # Normalise column names (strip whitespace)
    df.columns = df.columns.str.strip()

    missing = EXPECTED_COLUMNS - set(df.columns)
    if missing:
        logger.error(
            "FATAL — the downloaded xlsx does not contain the expected "
            "columns.\n"
            "  File   : %s\n"
            "  Missing: %s\n"
            "  Found  : %s\n"
            "The file structure may have changed. Please inspect the file "
            "and update the script accordingly.",
            path,
            sorted(missing),
            sorted(df.columns.tolist()),
        )
        sys.exit(1)

    # Clean up data
    df["Sector"] = df["Sector"].astype(str).str.strip()
    df["QP/Job Role Name"] = df["QP/Job Role Name"].astype(str).str.strip()
    df["NSQF Level"] = pd.to_numeric(df["NSQF Level"], errors="coerce")

    logger.info(
        "Loaded %d job roles across %d raw sectors.",
        len(df),
        df["Sector"].nunique(),
    )
    return df


def group_into_categories(
    df: pd.DataFrame,
    sector_map: dict[str, str] | None = None,
    descriptions: dict[str, str] | None = None,
    source_url: str = SOURCE_URL,
) -> pd.DataFrame:
    """Group job roles into broader NSQF categories.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain columns ``Sector``, ``QP/Job Role Name``,
        ``NSQF Level``.
    sector_map : dict, optional
        Mapping from raw sector names to category names.
        Defaults to :data:`SECTOR_TO_CATEGORY`.
    descriptions : dict, optional
        Descriptions keyed by category name.
        Defaults to :data:`CATEGORY_DESCRIPTIONS`.
    source_url : str
        URL to store in the ``source_url`` column.

    Returns
    -------
    pd.DataFrame
        Columns: ``category_name``, ``keywords``, ``description``,
        ``source_nsqf_level``, ``source_url``.
    """
    if sector_map is None:
        sector_map = SECTOR_TO_CATEGORY
    if descriptions is None:
        descriptions = CATEGORY_DESCRIPTIONS

    # Map sectors to categories
    df = df.copy()
    df["category"] = df["Sector"].map(sector_map)

    # Warn about unmapped sectors
    unmapped = df[df["category"].isna()]["Sector"].unique()
    if len(unmapped) > 0:
        logger.warning(
            "The following sectors have no category mapping and will be "
            "placed in 'Other': %s",
            sorted(unmapped.tolist()),
        )
        df["category"] = df["category"].fillna("Other")

    # Check distinct sector count
    distinct_sectors = df["Sector"].nunique()
    if distinct_sectors < 15:
        logger.warning(
            "Only %d distinct sectors found (expected ≥15). "
            "The grouping logic may need manual adjustment.",
            distinct_sectors,
        )

    # Aggregate per category
    rows: list[dict[str, str]] = []
    for cat_name, group in sorted(df.groupby("category")):
        keywords = sorted(group["QP/Job Role Name"].unique().tolist())
        levels = group["NSQF Level"].dropna()
        if len(levels) > 0:
            level_min = int(levels.min())
            level_max = int(levels.max())
            level_str = (
                str(level_min) if level_min == level_max
                else f"{level_min}-{level_max}"
            )
        else:
            level_str = ""

        desc = descriptions.get(cat_name, "")

        rows.append(
            {
                "category_name": cat_name,
                "keywords": "; ".join(keywords),
                "description": desc,
                "source_nsqf_level": level_str,
                "source_url": source_url,
            }
        )

    result = pd.DataFrame(rows)
    logger.info("Grouped into %d categories.", len(result))
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry-point: download → load → group → write CSV."""
    project_root = Path(__file__).resolve().parent.parent
    tmp_xlsx = project_root / "data" / "Job_Role_List.xlsx"
    output_csv = project_root / "data" / "nsqf_categories.csv"

    # 1. Download
    download_xlsx(SOURCE_URL, tmp_xlsx)

    # 2. Load & validate
    df = load_and_validate(tmp_xlsx)

    # 3. Group into categories
    result = group_into_categories(df)

    # 4. Validate result size
    n_categories = len(result)
    if n_categories < 20 or n_categories > 30:
        logger.warning(
            "Expected 20-30 categories but got %d. "
            "Review the SECTOR_TO_CATEGORY mapping.",
            n_categories,
        )

    # 5. Write CSV
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_csv, index=False)
    logger.info("Wrote %s (%d rows).", output_csv, len(result))

    # 6. Clean up downloaded xlsx
    try:
        tmp_xlsx.unlink()
        logger.info("Removed temporary file %s.", tmp_xlsx)
    except OSError:
        pass

    logger.info("Done.")


if __name__ == "__main__":
    main()
