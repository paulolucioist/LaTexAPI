import base64
import binascii
import os
import re
import subprocess
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List

from app.models.schemas import CompileRequest, CompileResponse


class CompilationError(RuntimeError):
    """Erro controlado durante compilação de documentos."""


def _sanitize_filename(filename: str) -> str:
    stem = Path(filename).stem or "document"
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", stem)
    return f"{safe}.tex"


def _sanitize_asset_path(filename: str) -> Path:
    stripped = filename.strip()
    if not stripped:
        raise CompilationError("Asset sem nome informado.")

    candidate = Path(stripped)
    if candidate.is_absolute():
        raise CompilationError("Assets não podem usar caminhos absolutos.")

    if any(part == ".." for part in candidate.parts):
        raise CompilationError("Assets não podem referenciar diretórios pais ('..').")

    sanitized_parts = [re.sub(r"[^A-Za-z0-9._/-]", "_", part) for part in candidate.parts]
    return Path(*sanitized_parts)


def _build_commands(tex_filename: str) -> List[List[str]]:
    return [
        [
            "latexmk",
            "-pdf",
            "-interaction=nonstopmode",
            "-halt-on-error",
            tex_filename,
        ],
        [
            "pdflatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            tex_filename,
        ],
    ]


def compile_document(request: CompileRequest) -> CompileResponse:
    start = time.perf_counter()

    if request.source_type != "latex":
        raise CompilationError(f"source_type '{request.source_type}' não é suportado.")

    filename = _sanitize_filename(request.filename)

    with TemporaryDirectory(prefix="latexapi-") as temp_dir:
        tex_path = Path(temp_dir) / filename
        tex_path.write_text(request.source, encoding="utf-8")
        _materialize_assets(temp_dir, request)

        compile_log = ""
        last_error: str | None = None

        for command in _build_commands(tex_path.name):
            try:
                result = subprocess.run(
                    command,
                    cwd=temp_dir,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=request.compile_timeout_seconds,
                    env={**os.environ, "TEXMFOUTPUT": temp_dir},
                )
                compile_log = (result.stdout or "") + (result.stderr or "")
                break
            except FileNotFoundError:
                last_error = f"Ferramenta '{command[0]}' não encontrada no sistema."
                continue
            except subprocess.TimeoutExpired:
                raise CompilationError(
                    f"Compilação excedeu {request.compile_timeout_seconds} segundos."
                )
            except subprocess.CalledProcessError as exc:
                compile_log = (exc.stdout or "") + (exc.stderr or "")
                last_error = "Compilação LaTeX falhou. Consulte o log retornado."
                continue
        else:
            error_message = last_error or "Falha desconhecida ao compilar o documento."
            raise CompilationError(error_message)

        pdf_path = tex_path.with_suffix(".pdf")
        if not pdf_path.exists():
            raise CompilationError("Arquivo PDF não foi gerado pela compilação.")

        pdf_bytes = pdf_path.read_bytes()
        encoded_pdf = base64.b64encode(pdf_bytes).decode("ascii")

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return CompileResponse(
            pdf_base64=encoded_pdf,
            elapsed_ms=elapsed_ms,
            log=compile_log if request.return_log else None,
            template_name=request.template_name,
        )


def _materialize_assets(temp_dir: str, request: CompileRequest) -> None:
    if not request.assets:
        return

    for asset in request.assets:
        asset_path = Path(temp_dir) / _sanitize_asset_path(asset.filename)
        asset_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            asset_bytes = base64.b64decode(asset.content_base64, validate=True)
        except binascii.Error as exc:  # type: ignore[arg-type]
            raise CompilationError(
                f"Asset '{asset.filename}' não é Base64 válido."
            ) from exc
        asset_path.write_bytes(asset_bytes)
