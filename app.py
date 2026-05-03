from __future__ import annotations

import io
import logging
import tempfile
import zipfile
from pathlib import Path

from flask import Flask, redirect, render_template, request, send_file, url_for
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from converter import COLUMN_MAPPING, convert_csv_file


MAX_UPLOAD_SIZE_BYTES = 16 * 1024 * 1024

log = logging.getLogger(__name__)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_SIZE_BYTES


@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


@app.context_processor
def asset_helpers() -> dict[str, object]:
    def static_asset_url(filename: str) -> str:
        static_file = Path(app.static_folder or "static") / filename
        version = int(static_file.stat().st_mtime) if static_file.exists() else 0
        return url_for("static", filename=filename, v=version)

    return {"static_asset_url": static_asset_url}


def normalize_output_name(filename: str) -> str:
    original = Path(secure_filename(filename) or "statement.csv")
    stem = original.stem or "statement"
    return f"ynab_{stem}.csv"


def convert_upload(upload: FileStorage) -> tuple[str, bytes]:
    if not upload.filename:
        raise ValueError("Uploaded file is missing a filename.")
    if not upload.filename.lower().endswith(".csv"):
        raise ValueError("Only CSV files are accepted.")

    output_name = normalize_output_name(upload.filename)

    with tempfile.TemporaryDirectory() as tmp_dir:
        input_path = Path(tmp_dir) / secure_filename(upload.filename)
        upload.save(input_path)

        ynab_df = convert_csv_file(str(input_path), COLUMN_MAPPING)
        buffer = io.StringIO()
        ynab_df.to_csv(buffer, index=False)
        return output_name, buffer.getvalue().encode("utf-8")


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/convert")
def convert_get():
    return redirect(url_for("index"))


@app.post("/convert")
def convert():
    uploads = [file for file in request.files.getlist("files") if file and file.filename]
    if not uploads:
        return render_template("index.html", error="Choose at least one CSV file to convert."), 400

    converted: list[tuple[str, bytes]] = []
    errors: list[str] = []

    for upload in uploads:
        try:
            converted.append(convert_upload(upload))
        except Exception:  # pragma: no cover - keeps UI resilient for unknown CSV variations
            filename = upload.filename or "unknown file"
            log.exception("Conversion failed for %s", filename)
            errors.append(f"{filename}: Could not be converted — check it is a valid UBS or Neon CSV export.")

    if not converted:
        return render_template("index.html", error="No files were converted.", errors=errors), 400

    if len(converted) == 1 and not errors:
        output_name, csv_bytes = converted[0]
        return send_file(
            io.BytesIO(csv_bytes),
            mimetype="text/csv",
            as_attachment=True,
            download_name=output_name,
        )

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        seen: dict[str, int] = {}
        for output_name, csv_bytes in converted:
            if output_name in seen:
                seen[output_name] += 1
                stem = Path(output_name).stem
                name = f"{stem}_{seen[output_name]}{Path(output_name).suffix}"
            else:
                seen[output_name] = 0
                name = output_name
            archive.writestr(name, csv_bytes)

        if errors:
            archive.writestr("conversion_report.txt", "\n".join(errors))

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name="ynab_converted_files.zip",
    )


if __name__ == "__main__":
    app.run()
