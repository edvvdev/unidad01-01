"""Audita los datasets descargados y publica `reports/audit_summary.json`.

La auditoría se calcula **desde los CSV** (tipos, nulos, duplicados y distribución
del target): es la fuente de verdad que las pruebas contrastan y que la ficha cita.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from inf8239_u01.data import DATASET_SPECS, audit_dataframe, load_dataset  # noqa: E402

REPORTS = ROOT / "reports"
DATA_RAW = ROOT / "data" / "raw"


def auditar(nombre: str) -> dict | None:
    """Audita un dataset descargado y devuelve su resumen (o None si no está)."""
    spec = DATASET_SPECS[nombre]
    ruta = DATA_RAW / f"{nombre}.csv"
    if not ruta.exists():
        print(f"[aviso] falta {ruta}: ejecuta download_dataset('{nombre}') antes")
        return None
    frame = load_dataset(nombre, ruta)
    auditoria = audit_dataframe(frame, spec["target"])
    numericas = [c for c, dtype in auditoria["dtypes"].items() if dtype.startswith(("int", "float"))]
    categoricas = [c for c in auditoria["dtypes"] if c not in numericas and c != spec["target"]]
    return {
        "nombre": spec["nombre"],
        "doi": spec["doi"],
        "licencia": spec["licencia"],
        "filas": auditoria["rows"],
        "columnas": auditoria["columns"],
        "n_numericas": len(numericas),
        "n_categoricas": len(categoricas),
        "columnas_numericas": numericas,
        "columnas_categoricas": categoricas,
        "total_nulos": auditoria["total_missing"],
        "nulos_por_columna": {k: v for k, v in auditoria["missing_per_column"].items() if v},
        "duplicate_rows": auditoria["duplicate_rows"],
        "target": spec["target"],
        "target_counts": auditoria.get("target_counts", {}),
    }


def main() -> Path:
    """Escribe `reports/audit_summary.json` y devuelve su ruta."""
    REPORTS.mkdir(exist_ok=True)
    resumen = {
        "generado_en": date.today().isoformat(),
        "datasets": {nombre: datos for nombre in sorted(DATASET_SPECS) if (datos := auditar(nombre))},
    }
    destino = REPORTS / "audit_summary.json"
    destino.write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")
    for nombre, datos in resumen["datasets"].items():
        print(f"{nombre}: {datos['filas']} filas x {datos['columnas']} columnas · "
              f"{datos['n_numericas']} numéricas + {datos['n_categoricas']} categóricas + target · "
              f"{datos['duplicate_rows']} duplicados")
    print("Auditoría guardada en", destino)
    return destino


if __name__ == "__main__":
    main()
