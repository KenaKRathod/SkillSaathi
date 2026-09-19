"""Tests for scripts/build_nsqf_categories.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import httpx
import pandas as pd
import pytest

# We import the module under test after adjusting the path so that the
# script can be imported without running __main__.
import importlib
import sys

# Ensure the scripts/ directory is importable.
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import build_nsqf_categories as bnc  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_job_roles_df() -> pd.DataFrame:
    """A small mock DataFrame simulating the NSDC Job Role List."""
    return pd.DataFrame(
        {
            "Sector": [
                "Agriculture",
                "Agriculture",
                "Textile Sector Skill Council",
                "Textile Sector Skill Council",
                "Apparel, Made-Ups & Home Furnishing",
                "Electronics",
                "Healthcare",
                "Life Sciences",
            ],
            "QP/Job Role Name": [
                "Pulses Cultivator",
                "Cotton Cultivator",
                "Blowroom Operator",
                "Carding Operator",
                "Self Employed Tailor",
                "PCB Assembly Operator",
                "General Duty Assistant",
                "Production Machine Operator",
            ],
            "NSQF Level": [4, 3, 3, 3, 4, 3, 4, 5],
        }
    )


# ---------------------------------------------------------------------------
# Test 1: Grouping produces expected category buckets
# ---------------------------------------------------------------------------


class TestGroupingFunction:
    """The grouping function, given a small mock dataframe of job roles,
    produces the expected category buckets."""

    def test_correct_categories_created(self, mock_job_roles_df: pd.DataFrame):
        """Each mock sector maps to the correct broader category."""
        result = bnc.group_into_categories(mock_job_roles_df)

        category_names = set(result["category_name"].tolist())
        expected = {
            "Agriculture & Farming",
            "Textiles & Tailoring",
            "Electronics & Hardware",
            "Healthcare & Life Sciences",
        }
        assert category_names == expected

    def test_keywords_contain_job_role_names(
        self, mock_job_roles_df: pd.DataFrame
    ):
        """Keywords for each category contain the underlying job-role names."""
        result = bnc.group_into_categories(mock_job_roles_df)

        agri_row = result[result["category_name"] == "Agriculture & Farming"]
        keywords = agri_row.iloc[0]["keywords"]
        assert "Pulses Cultivator" in keywords
        assert "Cotton Cultivator" in keywords

    def test_textiles_merges_two_sectors(
        self, mock_job_roles_df: pd.DataFrame
    ):
        """Textile Sector Skill Council and Apparel merge into one category."""
        result = bnc.group_into_categories(mock_job_roles_df)

        textile_row = result[
            result["category_name"] == "Textiles & Tailoring"
        ]
        assert len(textile_row) == 1
        keywords = textile_row.iloc[0]["keywords"]
        # Contains roles from both source sectors
        assert "Blowroom Operator" in keywords
        assert "Self Employed Tailor" in keywords

    def test_healthcare_merges_life_sciences(
        self, mock_job_roles_df: pd.DataFrame
    ):
        """Healthcare and Life Sciences merge into one category."""
        result = bnc.group_into_categories(mock_job_roles_df)

        hc_row = result[
            result["category_name"] == "Healthcare & Life Sciences"
        ]
        assert len(hc_row) == 1
        keywords = hc_row.iloc[0]["keywords"]
        assert "General Duty Assistant" in keywords
        assert "Production Machine Operator" in keywords

    def test_nsqf_level_ranges_correct(
        self, mock_job_roles_df: pd.DataFrame
    ):
        """NSQF level ranges are computed correctly (min-max)."""
        result = bnc.group_into_categories(mock_job_roles_df)

        agri_row = result[
            result["category_name"] == "Agriculture & Farming"
        ].iloc[0]
        # Agriculture has levels 3 and 4
        assert agri_row["source_nsqf_level"] == "3-4"

        elec_row = result[
            result["category_name"] == "Electronics & Hardware"
        ].iloc[0]
        # Electronics has only level 3
        assert elec_row["source_nsqf_level"] == "3"

        hc_row = result[
            result["category_name"] == "Healthcare & Life Sciences"
        ].iloc[0]
        # Healthcare 4 + Life Sciences 5
        assert hc_row["source_nsqf_level"] == "4-5"

    def test_source_url_populated(self, mock_job_roles_df: pd.DataFrame):
        """Every row has the source URL populated."""
        result = bnc.group_into_categories(mock_job_roles_df)
        for _, row in result.iterrows():
            assert row["source_url"] == bnc.SOURCE_URL
            assert len(row["source_url"]) > 0


# ---------------------------------------------------------------------------
# Test 2: CSV output integrity (using the full mapping against a
#          comprehensive mock that covers all 36 sectors)
# ---------------------------------------------------------------------------


class TestCSVOutputIntegrity:
    """The final CSV has 20-30 rows, no null category_name, no duplicate
    category_name, and every row has a non-empty source_url."""

    @pytest.fixture()
    def full_mapping_df(self) -> pd.DataFrame:
        """Build a DataFrame with at least one role per mapped sector."""
        rows = []
        for i, sector in enumerate(bnc.SECTOR_TO_CATEGORY.keys()):
            rows.append(
                {
                    "Sector": sector,
                    "QP/Job Role Name": f"Test Role {i}",
                    "NSQF Level": (i % 6) + 1,
                }
            )
        return pd.DataFrame(rows)

    def test_row_count_in_range(self, full_mapping_df: pd.DataFrame):
        """Output has between 20 and 30 rows."""
        result = bnc.group_into_categories(full_mapping_df)
        assert 20 <= len(result) <= 30, (
            f"Expected 20-30 categories, got {len(result)}"
        )

    def test_no_null_category_name(self, full_mapping_df: pd.DataFrame):
        """No category_name is null."""
        result = bnc.group_into_categories(full_mapping_df)
        assert result["category_name"].isna().sum() == 0

    def test_no_duplicate_category_name(self, full_mapping_df: pd.DataFrame):
        """No duplicate category_name values."""
        result = bnc.group_into_categories(full_mapping_df)
        assert result["category_name"].is_unique

    def test_every_row_has_source_url(self, full_mapping_df: pd.DataFrame):
        """Every row has a non-empty source_url."""
        result = bnc.group_into_categories(full_mapping_df)
        for _, row in result.iterrows():
            assert row["source_url"] is not None
            assert isinstance(row["source_url"], str)
            assert len(row["source_url"].strip()) > 0

    def test_every_row_has_keywords(self, full_mapping_df: pd.DataFrame):
        """Every row has non-empty keywords."""
        result = bnc.group_into_categories(full_mapping_df)
        for _, row in result.iterrows():
            assert row["keywords"] is not None
            assert len(row["keywords"].strip()) > 0

    def test_every_row_has_description(self, full_mapping_df: pd.DataFrame):
        """Every category in the mapping has a description."""
        result = bnc.group_into_categories(full_mapping_df)
        for _, row in result.iterrows():
            assert row["description"] is not None
            assert len(row["description"].strip()) > 0

    def test_expected_columns_present(self, full_mapping_df: pd.DataFrame):
        """Output DataFrame has exactly the expected columns."""
        result = bnc.group_into_categories(full_mapping_df)
        expected_cols = {
            "category_name",
            "keywords",
            "description",
            "source_nsqf_level",
            "source_url",
        }
        assert set(result.columns) == expected_cols


# ---------------------------------------------------------------------------
# Test 3: Failed download triggers hard failure, not silent empty CSV
# ---------------------------------------------------------------------------


class TestFailedDownloadHardFailure:
    """A mocked failed download triggers the hard-failure path, not a
    silent empty CSV."""

    def test_download_network_error_exits_nonzero(self, tmp_path: Path):
        """httpx network error causes SystemExit(1)."""
        with patch("build_nsqf_categories.httpx.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value.__enter__.return_value
            mock_client.get.side_effect = httpx.ConnectError(
                "Connection refused"
            )

            with pytest.raises(SystemExit) as exc_info:
                bnc.download_xlsx(bnc.SOURCE_URL, tmp_path / "test.xlsx")

            assert exc_info.value.code == 1

    def test_download_http_error_exits_nonzero(self, tmp_path: Path):
        """HTTP 404 error causes SystemExit(1)."""
        with patch("build_nsqf_categories.httpx.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value.__enter__.return_value
            mock_response = httpx.Response(
                status_code=404, request=httpx.Request("GET", bnc.SOURCE_URL)
            )
            mock_client.get.return_value = mock_response

            with pytest.raises(SystemExit) as exc_info:
                bnc.download_xlsx(bnc.SOURCE_URL, tmp_path / "test.xlsx")

            assert exc_info.value.code == 1

    def test_no_csv_produced_on_failure(self, tmp_path: Path):
        """On download failure, no output file is produced."""
        output = tmp_path / "test.xlsx"

        with patch("build_nsqf_categories.httpx.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value.__enter__.return_value
            mock_client.get.side_effect = httpx.ConnectError(
                "Connection refused"
            )

            with pytest.raises(SystemExit):
                bnc.download_xlsx(bnc.SOURCE_URL, output)

        assert not output.exists()

    def test_missing_columns_exits_nonzero(self, tmp_path: Path):
        """An xlsx missing expected columns causes SystemExit(1)."""
        # Create a minimal xlsx with wrong columns
        bad_df = pd.DataFrame(
            {"WrongColumn1": ["a"], "WrongColumn2": ["b"]}
        )
        bad_path = tmp_path / "bad.xlsx"
        bad_df.to_excel(bad_path, index=False)

        with pytest.raises(SystemExit) as exc_info:
            bnc.load_and_validate(bad_path)

        assert exc_info.value.code == 1
