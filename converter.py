from __future__ import annotations

from typing import Dict

import chardet
import pandas as pd


def detect_encoding(filepath: str) -> str:
    with open(filepath, "rb") as file:
        raw_data = file.read(10000)
    return chardet.detect(raw_data)["encoding"] or "utf-8"


def read_csv_with_encoding(filepath: str, skiprows: int, delimiter: str = ";") -> pd.DataFrame:
    encoding = detect_encoding(filepath)
    return pd.read_csv(filepath, delimiter=delimiter, skiprows=skiprows, encoding=encoding)


def standardize_column_names(df: pd.DataFrame, column_mapping: Dict[str, str]) -> pd.DataFrame:
    df.columns = [column_mapping.get(col, col) for col in df.columns]
    return df


def parse_amount_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def process_account_statement(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Date": pd.to_datetime(df["Abschlussdatum"]).dt.strftime("%Y-%m-%d"),
            "Payee": df["Beschreibung1"],
            "Memo": df["Beschreibung2"],
            "Outflow": df["Belastung"].abs(),
            "Inflow": df["Gutschrift"].abs(),
        }
    )


def process_credit_card_statement(df: pd.DataFrame) -> pd.DataFrame:
    # Booked rows: Belastung = charge, Gutschrift = reimbursement/credit.
    # Pending rows (neither set): positive Betrag = charge, negative Betrag = reimbursement.
    pending = df["Belastung"].isna() & df["Gutschrift"].isna()
    outflow = df["Belastung"].fillna(df["Betrag"].where(pending & df["Betrag"].gt(0)))
    inflow = df["Gutschrift"].fillna(df["Betrag"].abs().where(pending & df["Betrag"].lt(0)))

    return pd.DataFrame(
        {
            "Date": pd.to_datetime(df["Einkaufsdatum"], format="%d.%m.%Y").dt.strftime("%Y-%m-%d"),
            "Payee": df["Buchungstext"],
            "Memo": df["Branche"],
            "Outflow": outflow.abs(),
            "Inflow": inflow,
        }
    )


def process_neon_statement(df: pd.DataFrame) -> pd.DataFrame:
    amount = parse_amount_series(df["Amount"])

    return pd.DataFrame(
        {
            "Date": pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d"),
            "Payee": df["Description"].fillna(""),
            "Memo": df["Subject"].fillna(""),
            "Outflow": amount.where(amount < 0, 0).abs(),
            "Inflow": amount.where(amount > 0, 0).abs(),
        }
    )


def detect_csv_format(file_path: str) -> str:
    encoding = detect_encoding(file_path)

    with open(file_path, "r", encoding=encoding) as file:
        first_line = file.readline().strip()
        second_line = file.readline().strip()

    if first_line.startswith('"Date";"Amount"') or second_line.startswith('"Date";"Amount"'):
        return "neon"

    if "sep" in first_line:
        return "ubs_credit_card"

    return "ubs_account"


def convert_csv_file(file_path: str, column_mapping: Dict[str, str]) -> pd.DataFrame:
    csv_format = detect_csv_format(file_path)

    if csv_format == "neon":
        skiprows = 0
    elif csv_format == "ubs_credit_card":
        skiprows = 1
    else:
        skiprows = 9

    df = read_csv_with_encoding(file_path, skiprows=skiprows)

    if csv_format == "neon":
        return process_neon_statement(df)

    df = standardize_column_names(df, column_mapping)

    if csv_format == "ubs_credit_card":
        return process_credit_card_statement(df)

    return process_account_statement(df)


COLUMN_MAPPING: Dict[str, str] = {
    "Trade date": "Abschlussdatum",
    "Abschlussdatum": "Abschlussdatum",
    "Booking date": "Buchungsdatum",
    "Buchungsdatum": "Buchungsdatum",
    "Currency": "Währung",
    "Währung": "Währung",
    "Debit": "Belastung",
    "Belastung": "Belastung",
    "Credit": "Gutschrift",
    "Gutschrift": "Gutschrift",
    "Description1": "Beschreibung1",
    "Beschreibung1": "Beschreibung1",
    "Description2": "Beschreibung2",
    "Beschreibung2": "Beschreibung2",
    "Account number": "Kontonummer",
    "Kontonummer": "Kontonummer",
    "Card number": "Kartennummer",
    "Kartennummer": "Kartennummer",
    "Purchase date": "Einkaufsdatum",
    "Einkaufsdatum": "Einkaufsdatum",
    "Booking text": "Buchungstext",
    "Buchungstext": "Buchungstext",
    "Sector": "Branche",
    "Branche": "Branche",
    "Amount": "Betrag",
    "Betrag": "Betrag",
    "Booked": "Buchung",
    "Buchung": "Buchung",
}
