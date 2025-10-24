FROM python:3.11-slim-bookworm AS base

ARG TL_MIRROR=https://ftp.math.utah.edu/pub/tex/historic/systems/texlive/2024/tlnet-final

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TEXLIVE_YEAR=2024 \
    TEXLIVE_INSTALL_DIR=/usr/local/texlive/2024 \
    TEXLIVE_BIN_DIR=/usr/local/texlive/2024/bin/x86_64-linux \
    TL_MIRROR=${TL_MIRROR}

# Instala dependências base, TeX Live 2024 (via install-tl) e pacotes necessários.
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        fontconfig \
        ghostscript \
        perl \
        wget \
        xz-utils \
        make && \
    printf '%s\n' \
        'selected_scheme scheme-small' \
        'TEXDIR /usr/local/texlive/2024' \
        'TEXMFLOCAL /usr/local/texlive/texmf-local' \
        'TEXMFSYSCONFIG /usr/local/texlive/2024/texmf-config' \
        'TEXMFSYSVAR /usr/local/texlive/2024/texmf-var' \
        'TEXMFCONFIG /usr/local/texlive/2024/texmf-config' \
        'TEXMFVAR /usr/local/texlive/2024/texmf-var' \
        'binary_x86_64-linux 1' \
        'instopt_adjustpath 0' \
        'instopt_letter 0' \
        'instopt_portable 0' \
        'instopt_write18_restricted 1' \
        > /tmp/texlive.profile && \
    mkdir -p /tmp/install-tl && \
    curl -sSL ${TL_MIRROR}/install-tl-unx.tar.gz | \
        tar -xz -C /tmp/install-tl --strip-components=1 && \
    /tmp/install-tl/install-tl --repository ${TL_MIRROR} --profile=/tmp/texlive.profile && \
    $TEXLIVE_BIN_DIR/tlmgr option repository ${TL_MIRROR} && \
    $TEXLIVE_BIN_DIR/tlmgr update --self && \
    $TEXLIVE_BIN_DIR/tlmgr install \
        latexmk \
        babel-portuges \
        geometry \
        booktabs \
        siunitx \
        pgf \
        xcolor \
        beamer && \
    $TEXLIVE_BIN_DIR/fmtutil-sys --all && \
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
