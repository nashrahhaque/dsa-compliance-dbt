"""
Ingest Spotify DSA Transparency Report 2025 XLSX into DuckDB raw schema.
Also attempts to pull EU DSA API statements.
"""

import re
import sys
import warnings
from pathlib import Path

import duckdb
import pandas as pd
import requests

warnings.filterwarnings("ignore")

XLSX_PATH = Path(__file__).parent.parent / "data" / "Spotify Main Digital Services Act Transparency Report 2025.xlsx"
DESKTOP_PATH = Path.home() / "Desktop" / "Spotify Main Digital Services Act Transparency Report 2025.xlsx"
DB_PATH = Path(__file__).parent.parent / "dev.duckdb"
SEEDS_DIR = Path(__file__).parent.parent / "seeds"

EU_DSA_API = "https://transparency.dsa.ec.europa.eu/api/v1/statements"

COLUMN_MAPS = {
    "own_initiative_illegal": {
        "Applicability": "applicability",
        "Service": "service",
        "Reporting period": "reporting_period",
        "Category of illegal content": "category_of_illegal_content",
        'Description of the sub-category "Other"': "sub_category_other",
        "Number of measures taken at the provider's own initiative ": "num_measures_own_initiative",
        "Number of measures taken after detection with solely automated means ": "num_measures_automated",
        "Visibility restriction Removal": "visibility_removal",
        "Visibility restriction Disable": "visibility_disable",
        "Visibility restriction Demoted": "visibility_demoted",
        "Visibility restriction Age restricted": "visibility_age_restricted",
        "Visibility restriction Interaction restricted": "visibility_interaction_restricted",
        "Visibility restriction Labelled ": "visibility_labelled",
        "Visibility restriction Other": "visibility_other",
        "Monetary restriction Suspension": "monetary_suspension",
        "Monetary restriction Termination": "monetary_termination",
        "Monetary restriction Other": "monetary_other",
        "Provision of the service Suspension": "service_suspension",
        "Provision of the service Termination": "service_termination",
        "Account restriction Suspension": "account_suspension",
        "Account restriction Termination": "account_termination",
    },
    "own_initiative_tc": {
        "Applicability": "applicability",
        "Service": "service",
        "Reporting period": "reporting_period",
        "Category of incompatibility with the provider's terms and conditions": "category_tc",
        'Description of the sub-category "Other"': "sub_category_other",
        "Number of measures taken at the provider's own initiative ": "num_measures_own_initiative",
        "Number of measures taken after detection with solely automated means ": "num_measures_automated",
        "Visibility restriction Removal": "visibility_removal",
        "Visibility restriction Disable": "visibility_disable",
        "Visibility restriction Demoted": "visibility_demoted",
        "Visibility restriction Age restricted": "visibility_age_restricted",
        "Visibility restriction Interaction restricted": "visibility_interaction_restricted",
        "Visibility restriction Labelled ": "visibility_labelled",
        "Visibility restriction Other": "visibility_other",
        "Monetary restriction Suspension": "monetary_suspension",
        "Monetary restriction Termination": "monetary_termination",
        "Monetary restriction Other": "monetary_other",
        "Provision of the service Suspension": "service_suspension",
        "Provision of the service Termination": "service_termination",
        "Account restriction Suspension": "account_suspension",
        "Account restriction Termination": "account_termination",
    },
    "appeals": {
        "Applicability": "applicability",
        "Service": "service",
        "Reporting period": "reporting_period",
        "Section": "section",
        "Indicator": "indicator",
        "Scope": "scope",
        "Value": "value",
        "Contextual Information": "contextual_information",
    },
    "automated_means": {
        "Applicability": "applicability",
        "Service": "service",
        "Reporting period": "reporting_period",
        "Section": "section",
        "Indicator": "indicator",
        "Scope": "scope",
        "Value": "value",
        "Contextual Information": "contextual_information",
    },
    "member_states_orders": {
        "Applicability": "applicability",
        "Service": "service",
        "Reporting period": "reporting_period",
        "Category of illegal content": "category_of_illegal_content",
        'Description of the sub-category "Other"': "sub_category_other",
        "Scope": "scope",
        "Number of orders to act against illegal content received": "num_orders_against_illegal",
        "Number of specific items of information included in the total number of orders to act against illegal content": "num_items_in_orders",
        "Median time to inform the authority of the receipt of the order to act against illegal content": "median_time_inform_authority_act",
        "Median time to give effect to the order to act against illegal content": "median_time_give_effect_act",
        "Number of orders to provide information": "num_orders_provide_info",
        "Median time to inform the authority of the receipt of the order to provide information": "median_time_inform_authority_info",
        "Median time to give effect to the order to provide information": "median_time_give_effect_info",
    },
    "notices": {
        "Applicability": "applicability",
        "Service": "service",
        "Reporting period": "reporting_period",
        "Category of illegal content": "category_of_illegal_content",
        'Description of the sub-category "Other"': "sub_category_other",
        "Number of notices received ": "num_notices_received",
        "Number of notices received from Trusted flaggers": "num_notices_trusted_flaggers",
        "Number of specific items of information included in the total number of notices": "num_items_in_notices",
        "Number of specific items of information included in the total number of notices by Trusted Flaggers (Trusted Flagger notices)": "num_items_trusted_flaggers",
        "Median time to take action": "median_time_to_action",
        "Median time to take action (Trusted Flagger notices)": "median_time_to_action_tf",
        "Number of actions taken on the basis of the law": "num_actions_law",
        "Number of actions taken on the basis of the law (Trusted Flagger notices)": "num_actions_law_tf",
        "Number of actions taken on the basis of the terms and conditions of the service": "num_actions_tc",
        "Number of actions taken on the basis of the terms and conditions of the service (Trusted Flagger notices)": "num_actions_tc_tf",
    },
    "categories": {
        "Category label": "category_label",
        "Category description": "category_description",
        "Category of illegal content / incompatible with the terms and conditions": "category_code",
        "Contextual information": "contextual_information",
    },
}

SHEET_MAP = {
    "5_own_initiative_illegal": "own_initiative_illegal",
    "6_own_initiative_TC": "own_initiative_tc",
    "7_appeals_and_recidivism": "appeals",
    "8_automated_means": "automated_means",
    "3_member_states_orders": "member_states_orders",
    "4_notices": "notices",
    "2_categories_names": "categories",
}


def load_xlsx():
    path = DESKTOP_PATH if DESKTOP_PATH.exists() else XLSX_PATH
    if not path.exists():
        print(f"ERROR: XLSX not found at {path}", file=sys.stderr)
        sys.exit(1)
    print(f"Reading XLSX: {path}")
    return pd.read_excel(path, sheet_name=None)


def apply_column_map(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    col_map = COLUMN_MAPS[table_name]
    df = df.rename(columns=col_map)
    keep_cols = list(col_map.values())
    existing = [c for c in keep_cols if c in df.columns]
    return df[existing].copy()


def fetch_eu_dsa_api() -> pd.DataFrame | None:
    print("\nAttempting EU DSA API...")
    try:
        resp = requests.get(
            EU_DSA_API,
            params={"platform_name": "Spotify", "limit": 1000},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        records = data if isinstance(data, list) else data.get("results", data.get("data", []))
        if not records:
            print("  WARNING: EU DSA API returned empty results  -  skipping.")
            return None
        df = pd.DataFrame(records)
        print(f"  EU DSA API: {len(df)} records retrieved.")
        return df
    except Exception as e:
        print(f"  WARNING: EU DSA API unavailable ({e})  -  skipping.")
        return None


def write_to_duckdb(con: duckdb.DuckDBPyConnection, df: pd.DataFrame, table: str):
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    con.execute(f"DROP TABLE IF EXISTS raw.{table}")
    con.register("_tmp", df)
    con.execute(f"CREATE TABLE raw.{table} AS SELECT * FROM _tmp")
    con.unregister("_tmp")


def main():
    SEEDS_DIR.mkdir(exist_ok=True)

    all_sheets = load_xlsx()
    con = duckdb.connect(str(DB_PATH))

    loaded = {}

    for sheet_name, table_name in SHEET_MAP.items():
        if sheet_name not in all_sheets:
            print(f"  WARNING: Sheet '{sheet_name}' not found  -  skipping.")
            continue

        df = all_sheets[sheet_name]
        df = apply_column_map(df, table_name)

        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].astype(str).str.strip().replace("nan", None)

        write_to_duckdb(con, df, table_name)

        seed_path = SEEDS_DIR / f"{table_name}.csv"
        df.to_csv(seed_path, index=False)
        loaded[table_name] = len(df)
        print(f"  {table_name}: {len(df)} rows → raw.{table_name} + seeds/{table_name}.csv")

    eu_df = fetch_eu_dsa_api()
    if eu_df is not None:
        write_to_duckdb(con, eu_df, "eu_dsa_statements")
        eu_df.to_csv(SEEDS_DIR / "eu_dsa_statements.csv", index=False)
        loaded["eu_dsa_statements"] = len(eu_df)
        print(f"  eu_dsa_statements: {len(eu_df)} rows → raw.eu_dsa_statements")

    con.close()

    print("\n=== Ingestion Summary ===")
    for table, rows in loaded.items():
        print(f"  {table}: {rows} rows")
    print(f"\nDuckDB: {DB_PATH}")
    print(f"Seeds:  {SEEDS_DIR}")


if __name__ == "__main__":
    main()
