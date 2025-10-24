from typing import List, Literal, Optional

from pydantic import BaseModel, Field, constr


class AssetItem(BaseModel):
    filename: constr(strip_whitespace=True, min_length=1, max_length=128)  # type: ignore[valid-type]
    content_base64: constr(min_length=1)  # type: ignore[valid-type]


class CompileRequest(BaseModel):
    """Payload mínimo aceito no endpoint /compile."""

    source: constr(min_length=1, max_length=200_000)  # type: ignore[valid-type]
    source_type: Literal["latex"] = "latex"
    output_format: Literal["pdf_base64"] = "pdf_base64"
    filename: constr(strip_whitespace=True, min_length=1, max_length=64) = "document.tex"  # type: ignore[valid-type]
    compile_timeout_seconds: int = Field(default=20, ge=1, le=120)
    return_log: bool = False
    assets: List[AssetItem] = Field(default_factory=list, max_length=32)
    template_name: Optional[constr(strip_whitespace=True, max_length=64)] = None  # type: ignore[valid-type]


class CompileResponse(BaseModel):
    pdf_base64: str
    elapsed_ms: int
    log: Optional[str] = None
    template_name: Optional[str] = None
