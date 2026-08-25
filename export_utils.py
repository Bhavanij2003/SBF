
import pandas as pd
import os
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORT_DIR = os.path.join(BASE_DIR, "data", "exports")


def _ensure_dir():
    os.makedirs(EXPORT_DIR, exist_ok=True)


def export_to_csv(rows, filename_prefix="sbf_export"):
    _ensure_dir()
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(EXPORT_DIR, f"{filename_prefix}_{ts}.csv")
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)
    return path


def export_to_excel(rows, filename_prefix="sbf_export"):
    _ensure_dir()
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(EXPORT_DIR, f"{filename_prefix}_{ts}.xlsx")
    df = pd.DataFrame(rows)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Applications")
        worksheet = writer.sheets["Applications"]
        for i, col in enumerate(df.columns, start=1):
            max_len = max([len(str(col))] + [len(str(v)) for v in df[col].astype(str)][:200])
            worksheet.column_dimensions[worksheet.cell(row=1, column=i).column_letter].width = min(40, max_len + 2)
    return path
