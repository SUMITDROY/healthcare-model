FROM python:3.12-slim
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
ENTRYPOINT ["python", "-m", "coder.cli"]
