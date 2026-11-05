FROM python:3.12-slim@sha256:e695ab189fa2d082b1c61c69a6b888a5adeca61ceeccad107b1ed2a125721a9e
ENV OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY coder coder
COPY data data
COPY scripts scripts
COPY tests tests
COPY score.py .
RUN python -m coder.train
COPY third_party/ATTRIBUTION.md third_party/MTS-Dialog-LICENSE.txt third_party/
COPY third_party/WHO-ICD11-LICENSE.pdf third_party/who-source*.json third_party/
ENTRYPOINT ["python", "-m", "coder.cli"]
