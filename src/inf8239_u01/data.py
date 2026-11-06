"""Carga, auditoría y descarga reproducible de datos (LAB01 y LAB02)."""

from __future__ import annotations

import hashlib
import io
import zipfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import pandas as pd

ALLOWED_SCHEMES = {"http", "https"}

#: Identificador enviado en la petición HTTP para que el servidor identifique la descarga.
USER_AGENT = "inf8239-u01/1.0 (INF-8239 Ciencia de Datos II, UASD)"


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


def sha256_bytes(data: bytes) -> str:
    """SHA-256 de un bloque de bytes en hexadecimal."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    """SHA-256 de un archivo en disco, leído por bloques."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


#: Raíz del proyecto (padre de `src/`), usada para escribir rutas verificables.
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _sidecar_path(path: Path) -> str:
    """Ruta del archivo tal como puede verificarla `sha256sum -c` desde la raíz.

    Si el archivo está dentro del proyecto se guarda la ruta relativa a la raíz
    (`data/raw/adult.csv`); si está fuera, se guarda la ruta absoluta. En ambos casos
    `sha256sum -c` encuentra el archivo desde el directorio de trabajo.
    """
    resolved = path.resolve()
    try:
        return resolved.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def write_sha256_sidecar(path: str | Path, digest: str | None = None) -> Path:
    """Escribe `<archivo>.sha256` con el SHA-256 de **ese** archivo.

    El sidecar usa el formato de `sha256sum -c` (`<hash>  <ruta>`) y guarda la ruta
    relativa al directorio de trabajo, de modo que `sha256sum -c data/raw/*.sha256`
    verifica cada archivo desde la raíz del proyecto.
    """
    target = Path(path)
    if digest is None:
        digest = sha256_file(target)
    sidecar = target.with_name(target.name + ".sha256")
    sidecar.write_text(f"{digest}  {_sidecar_path(target)}\n", encoding="utf-8")
    return sidecar


def _download_bytes(url: str, timeout: int) -> bytes:
    """Descarga el contenido de una URL http(s) usando solo la biblioteca estándar.

    Se usa `urllib.request` y no `requests` para que el proyecto funcione con
    `uv sync --frozen` sin depender de ningún paquete no declarado.
    """
    validate_url(url)
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.read()
    except HTTPError as error:
        raise RuntimeError(f"La descarga devolvió el estado {error.code}: {url}") from error
    except URLError as error:
        raise RuntimeError(f"No se pudo descargar {url}: {error.reason}") from error


def download_csv(url: str, destination: str | Path, filename: str | None = None) -> Path:
    """Descarga un CSV y lo guarda en disco devolviendo su ruta.

    Valida la URL, comprueba que el archivo descargado sea legible, no vacío y
    contenga al menos una columna y una fila. Deja además el sidecar `.sha256`
    con el hash **de ese archivo**.
    """
    content = _download_bytes(url, timeout=120)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    if filename is None:
        filename = Path(urlparse(url).path).name or "dataset.csv"
    target = destination / filename
    target.write_bytes(content)
    if target.stat().st_size == 0:
        raise ValueError(f"El archivo descargado está vacío: {target}")
    frame = pd.read_csv(target)
    if frame.empty or frame.shape[1] == 0:
        raise ValueError(f"El archivo descargado no contiene datos utilizables: {target}")
    write_sha256_sidecar(target)
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
        "doi": "10.24432/C5XW20",
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
        "doi": "10.24432/C5K306",
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

    Guarda además el ZIP original y **un sidecar `.sha256` por archivo** (el del ZIP y el
    del CSV), cada uno con el hash de ese archivo, de forma que
    `sha256sum -c data/raw/*.sha256` verifica los dos desde la raíz del proyecto.
    """
    if name not in DATASET_SPECS:
        raise ValueError(f"Dataset desconocido: {name}. Opciones: {sorted(DATASET_SPECS)}")
    spec = DATASET_SPECS[name]
    url = validate_url(spec["url"])
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)

    content = _download_bytes(url, timeout=180)
    archive_path = destination / f"{name}.zip"
    archive_path.write_bytes(content)
    write_sha256_sidecar(archive_path, sha256_bytes(content))

    archive = zipfile.ZipFile(io.BytesIO(content))
    frame = _read_adult(archive) if name == "adult" else _read_bank(archive)
    frame = frame.apply(lambda column: column.str.strip() if column.dtype == object else column)

    target = destination / f"{name}.csv"
    frame.to_csv(target, index=False)
    write_sha256_sidecar(target)

    nombre_original = Path(urlparse(url).path).name
    (destination / f"{target.name}.source.txt").write_text(
        f"dataset: {spec['nombre']}\nurl: {spec['url']}\nficha: {spec['ficha']}\n"
        f"doi: {spec['doi']}\nlicencia: {spec['licencia']}\n"
        f"archivo original: {nombre_original}\n"
        f"zip local: {archive_path.name}\nsha256 del zip: {sha256_bytes(content)}\n"
        f"csv local: {target.name}\nsha256 del csv: {sha256_file(target)}\n",
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
