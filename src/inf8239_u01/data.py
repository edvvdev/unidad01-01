"""Carga, auditoría y descarga reproducible de datos (LAB01 y LAB02)."""

from __future__ import annotations

import hashlib
import io
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

ALLOWED_SCHEMES = {"http", "https"}


def load_breast_cancer() -> tuple[pd.DataFrame, pd.Series]:
    """Carga el dataset de diagnóstico de cáncer de mama de scikit-learn.

    Devuelve X (30 variables predictoras) e y (etiqueta binaria: maligno=0, benigno=1).
    """
    from sklearn.datasets import load_breast_cancer

    bunch = load_breast_cancer()
    frame = pd.DataFrame(bunch.data, columns=list(bunch.feature_names))
    target = pd.Series(bunch.target, name="target")
    return frame, target


def audit_dataframe(frame: pd.DataFrame, target_column: str | None = None) -> dict:
    """Auditoría: tipos, nulos, porcentaje ausente, valores únicos y duplicados."""
    missing = frame.isna().sum()
    unique = frame.nunique(dropna=True)
    report = {
        "rows": int(frame.shape[0]),
        "columns": int(frame.shape[1]),
        "column_names": list(frame.columns),
        "dtypes": {column: str(dtype) for column, dtype in frame.dtypes.items()},
        "missing_per_column": {column: int(value) for column, value in missing.items()},
        "missing_percent": {column: float(value / len(frame) * 100) for column, value in missing.items()},
        "total_missing": int(missing.sum()),
        "unique_per_column": {column: int(value) for column, value in unique.items()},
        "duplicate_rows": int(frame.duplicated().sum()),
    }
    if target_column and target_column in frame.columns:
        counts = frame[target_column].value_counts().sort_index()
        report["target_counts"] = {str(key): int(value) for key, value in counts.items()}
        report["target_classes"] = int(counts.size)
        report["target_distribution"] = {str(key): float(value / len(frame)) for key, value in counts.items()}
    return report


def audit_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Auditoría en forma de tabla (una fila por columna)."""
    rows = []
    for column in frame.columns:
        values = frame[column]
        rows.append(
            {
                "columna": column,
                "tipo": str(values.dtype),
                "nulos": int(values.isna().sum()),
                "porcentaje_nulos": round(float(values.isna().mean() * 100), 3),
                "valores_unicos": int(values.nunique(dropna=True)),
                "ejemplo": str(values.dropna().iloc[0]) if values.notna().any() else "",
            }
        )
    return pd.DataFrame(rows)


def validate_url(url: str) -> str:
    """Valida que la URL sea http(s) y devuelva la URL normalizada."""
    parsed = urlparse(url)
    if parsed.scheme.lower() not in ALLOWED_SCHEMES or not parsed.netloc:
        raise ValueError(f"URL no válida para descarga: {url}")
    return url


def download_csv(url: str, destination: str | Path, filename: str | None = None) -> Path:
    """Descarga un CSV y lo guarda en disco devolviendo su ruta.

    Valida la URL, comprueba que el archivo descargado sea legible, no vacío y
    contenga al menos una columna y una fila.
    """
    import requests

    validate_url(url)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    digest = hashlib.sha256(response.content).hexdigest()
    if filename is None:
        filename = Path(urlparse(url).path).name or "dataset.csv"
    target = destination / filename
    target.write_bytes(response.content)
    if target.stat().st_size == 0:
        raise ValueError(f"El archivo descargado está vacío: {target}")
    frame = pd.read_csv(target)
    if frame.empty or frame.shape[1] == 0:
        raise ValueError(f"El archivo descargado no contiene datos utilizables: {target}")
    (destination / f"{target.name}.sha256").write_text(f"{digest}  {target.name}\n", encoding="utf-8")
    return target


def extract_zip_members(zip_path: str | Path, destination: str | Path) -> list[Path]:
    """Extrae un ZIP descargado (UCI distribuye sus datasets en ZIP) de forma segura."""
    zip_path = Path(zip_path)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    extracted = []
    with zipfile.ZipFile(zip_path) as archive:
        root = destination.resolve()
        for member in archive.infolist():
            target = (destination / member.filename).resolve()
            if root not in target.parents and target != root:
                raise ValueError(f"Ruta insegura en ZIP: {member.filename}")
            archive.extract(member, destination)
            extracted.append(target)
    return extracted


ADULT_COLUMNS = [
    "age", "workclass", "fnlwgt", "education", "education_num", "marital_status",
    "occupation", "relationship", "race", "sex", "capital_gain", "capital_loss",
    "hours_per_week", "native_country", "income",
]

# Especificación de los dos datasets candidatos del LAB02.
# `exclude` recoge exclusiones justificadas semánticamente (no por su efecto en la métrica).
DATASET_SPECS: dict[str, dict] = {
    "adult": {
        "nombre": "Adult (Census Income)",
        "url": "https://archive.ics.uci.edu/static/public/2/adult.zip",
        "ficha": "https://archive.ics.uci.edu/dataset/2/adult",
        "licencia": "CC BY 4.0 (UCI)",
        "target": "income",
        "target_positive": ">50K",
        "exclude": ["fnlwgt", "race", "sex", "native_country"],
        "motivo_exclusion": (
            "fnlwgt es un peso de muestreo del censo, no un atributo de la persona; "
            "race, sex y native_country son atributos sensibles que el modelo no necesita para "
            "estimar el ingreso y cuyo uso exigiría justificación de equidad"
        ),
    },
    "bank": {
        "nombre": "Bank Marketing",
        "url": "https://archive.ics.uci.edu/static/public/222/bank+marketing.zip",
        "ficha": "https://archive.ics.uci.edu/dataset/222/bank-marketing",
        "licencia": "CC BY 4.0 (UCI)",
        "target": "y",
        "target_positive": "yes",
        "exclude": ["duration"],
        "motivo_exclusion": (
            "duration es la duración de la llamada: solo se conoce después de la llamada, "
            "por lo que no está disponible en el momento de decidir (fuga de información)"
        ),
    },
}


def _read_adult(archive) -> pd.DataFrame:
    frames = []
    for member in ["adult.data", "adult.test"]:
        with archive.open(member) as handle:
            if member == "adult.test":
                # adult.test empieza con la línea de comentario '|1x3 Cross validator'
                # y termina con una fila de encabezado ('.') que no es un dato
                frame = pd.read_csv(handle, header=None, skipinitialspace=True, na_values="?", skiprows=1)
                frame = frame[~frame.apply(lambda row: all(str(value).strip() == "." for value in row), axis=1)]
            else:
                frame = pd.read_csv(handle, header=None, skipinitialspace=True, na_values="?")
        frame.columns = ADULT_COLUMNS
        frames.append(frame)
    combined = pd.concat(frames, ignore_index=True)
    combined["income"] = combined["income"].astype(str).str.replace(".", "", regex=False)
    return combined


def _read_bank(archive) -> pd.DataFrame:
    """UCI distribuye este dataset en ZIP anidados: bank.zip contiene bank-full.csv."""
    with archive.open("bank.zip") as inner_handle:
        inner = zipfile.ZipFile(io.BytesIO(inner_handle.read()))
    with inner.open("bank-full.csv") as handle:
        frame = pd.read_csv(handle, sep=";", na_values="unknown")
    return frame


def download_dataset(name: str, destination: str | Path = "data/raw") -> Path:
    """Descarga un dataset candidato y deja un único CSV limpio en `destination`.

    Guarda además el SHA-256 de los bytes descargados para poder verificar la procedencia.
    """
    import requests

    if name not in DATASET_SPECS:
        raise ValueError(f"Dataset desconocido: {name}. Opciones: {sorted(DATASET_SPECS)}")
    spec = DATASET_SPECS[name]
    url = validate_url(spec["url"])
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, timeout=180)
    response.raise_for_status()
    digest = hashlib.sha256(response.content).hexdigest()
    archive = zipfile.ZipFile(io.BytesIO(response.content))
    frame = _read_adult(archive) if name == "adult" else _read_bank(archive)
    frame = frame.apply(lambda column: column.str.strip() if column.dtype == object else column)
    target = Path(destination) / f"{name}.csv"
    frame.to_csv(target, index=False)
    (destination / f"{target.name}.sha256").write_text(f"{digest}  {target.name}\n", encoding="utf-8")
    (destination / f"{target.name}.source.txt").write_text(
        f"dataset: {spec['nombre']}\nurl: {spec['url']}\nficha: {spec['ficha']}\n"
        f"licencia: {spec['licencia']}\nsha256 del archivo descargado: {digest}\n",
        encoding="utf-8",
    )
    return target


def load_dataset(name: str, path: str | Path | None = None) -> pd.DataFrame:
    """Carga el CSV local del dataset indicado."""
    if name not in DATASET_SPECS:
        raise ValueError(f"Dataset desconocido: {name}. Opciones: {sorted(DATASET_SPECS)}")
    path = Path(path) if path is not None else Path("data/raw") / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"No se encuentra {path}. Ejecute antes: download_dataset('{name}')"
        )
    return pd.read_csv(path)
