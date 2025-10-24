from fastapi import FastAPI, HTTPException

from app.models.schemas import CompileRequest, CompileResponse
from app.services.compiler import CompilationError, compile_document


app = FastAPI(
    title="LatexAPI",
    version="0.1.0",
    description=(
        "Serviço enxuto para compilação LaTeX síncrona em PDF. "
        "Pensado para evoluir facilmente para workers ou filas dedicadas."
    ),
)


@app.post("/compile", response_model=CompileResponse, summary="Compila documento LaTeX")
async def compile_endpoint(payload: CompileRequest) -> CompileResponse:
    try:
        compilation = compile_document(payload)
    except CompilationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return compilation
