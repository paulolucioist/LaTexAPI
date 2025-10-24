FROM python:3.11-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TEXLIVE_YEAR=2024 \
    TEXLIVE_INSTALL_DIR=/usr/local/texlive/2024 \
    TEXLIVE_BIN_DIR=/usr/local/texlive/2024/bin/x86_64-linux

# Instala dependências base, TeX Live 2024 (via install-tl) e pacotes necessários.
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        fontconfig \
        ghostscript \
        perl \
        wget \
        latexmk \
        make && \
    printf '%s\n' \
        'selected_scheme scheme-small' \
        'TEXLIVE_INSTALL_PREFIX /usr/local/texlive' \
        'TEXLIVE_YEAR 2024' \
        'binary_x86_64-linux 1' \
        'instopt_adjustpath 0' \
        'instopt_letter 0' \
        'instopt_portable 0' \
        'instopt_write18_restricted 1' \
        > /tmp/texlive.profile && \
    mkdir -p /tmp/install-tl && \
    curl -sSL http://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz | \
        tar -xz -C /tmp/install-tl --strip-components=1 && \
    /tmp/install-tl/install-tl --profile=/tmp/texlive.profile && \
    $TEXLIVE_BIN_DIR/tlmgr option repository http://mirror.ctan.org/systems/texlive/tlnet && \
    $TEXLIVE_BIN_DIR/tlmgr update --self && \
    $TEXLIVE_BIN_DIR/tlmgr install \
        collection-latexrecommended \
        collection-fontsrecommended \
        collection-langportuguese \
        collection-latexextra \
        collection-pictures \
        collection-mathscience \
        beamer && \
    rm -rf /tmp/install-tl /tmp/texlive.profile && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Configura PATH para incluir TeX Live.
ENV PATH="$TEXLIVE_BIN_DIR:${PATH}"

WORKDIR /app

# Copia definição de dependências e instala em modo virtualenv isolado.
COPY pyproject.toml ./
COPY app ./app
RUN python -m venv /.venv && \
    /.venv/bin/pip install --upgrade pip && \
    /.venv/bin/pip install .

ENV PATH="/.venv/bin:${PATH}"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
