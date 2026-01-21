from dataclasses import dataclass
from typing import Optional

@dataclass
class Course:
    """Pure entity representing a SISU course mapping."""
    co_curso: str
    no_curso: str

@dataclass
class SisuVacancy:
    """
    Pure entity representing a specific college vacancy.
    Fields maintain original Portuguese names from the API for semantic consistency.
    """
    co_oferta: str
    sg_ies: str
    no_municipio_campus: str
    sg_uf_campus: str
    no_curso: str
    nu_nota_corte: Optional[float] = None