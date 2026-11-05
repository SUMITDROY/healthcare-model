"""Offline benchmark. A socket guard makes accidental network use fail."""
import argparse
import hashlib
import json
import os
import platform
import resource
import socket
import sys
import time
from pathlib import Path

# Scripts are executable directly from repo root or inside the container.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def blocked(*args, **kwargs):
    raise RuntimeError('Network forbidden during offline benchmark')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', default='data/external_200.jsonl')
    p.add_argument('--output', default='reports/external-predictions.jsonl')
    p.add_argument('--report', default='reports/benchmark.json')
    p.add_argument('--model', default='artifacts/offline.joblib')
    a = p.parse_args()
    for name in ('OPENAI_API_KEY', 'ANTHROPIC_API_KEY'):
        os.environ.pop(name, None)
    socket.socket.connect = blocked
    socket.socket.connect_ex = blocked
    socket.create_connection = blocked
    start = time.perf_counter()
    cpu_start = time.process_time()
    from coder.engine import OfflineCoder, rows
    inputs = rows(a.input)
    model = OfflineCoder.load(a.model)
    Path(a.output).parent.mkdir(parents=True, exist_ok=True)
    times = []
    predictions = []
    with open(a.output, 'w', encoding='utf-8', buffering=1) as f:
        for row in inputs:
            t = time.perf_counter()
            codes, _ = model.predict(row['text'])
            times.append(time.perf_counter()-t)
            prediction = {'id': row['id'], 'codes': codes}
            predictions.append(prediction)
            f.write(json.dumps(prediction, ensure_ascii=False)+'\n')
            f.flush()
    elapsed = time.perf_counter()-start
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_bytes = peak if sys.platform == 'darwin' else peak * 1024
    valid = set(model.codes)
    train_hashes = {hashlib.sha256(r['text'].encode()).hexdigest() for r in model.examples}
    overlap = sum(hashlib.sha256(r['text'].encode()).hexdigest() in train_hashes for r in inputs)
    sorted_times = sorted(times)
    def cgroup(name):
        path = Path('/sys/fs/cgroup')/name
        return path.read_text().strip() if path.exists() else None
    result = {
        'benchmark_type': 'external throughput and output validity; NOT coding accuracy',
        'source': 'MTS-Dialog TestSet-1, 200 unmodified dialogue texts',
        'input_sha256': hashlib.sha256(Path(a.input).read_bytes()).hexdigest(),
        'input_notes': len(inputs), 'output_notes': len(predictions),
        'unique_input_ids': len({r['id'] for r in inputs}),
        'unique_input_texts': len({r['text'] for r in inputs}),
        'missing_ids': len({r['id'] for r in inputs}-{r['id'] for r in predictions}),
        'invalid_codes': sum(c not in valid for r in predictions for c in r['codes']),
        'empty_predictions': sum(not r['codes'] for r in predictions),
        'exact_text_training_overlap': overlap,
        'wall_seconds_including_import_and_model_load': round(elapsed, 4),
        'cpu_seconds': round(time.process_time()-cpu_start, 4),
        'peak_process_rss_mib': round(peak_bytes/(1024**2), 2),
        'cgroup_cpu_max': cgroup('cpu.max'),
        'cgroup_memory_max_bytes': cgroup('memory.max'),
        'cgroup_memory_peak_bytes': cgroup('memory.peak'),
        'per_note_mean_ms_excluding_startup': round(sum(times)/max(len(times),1)*1000, 3),
        'per_note_p95_ms_excluding_startup': round(sorted_times[min(int(.95*len(times)),len(times)-1)]*1000, 3),
        'within_10_minutes': elapsed <= 600,
        'api_calls': 0, 'api_cost_usd': 0,
        'training_examples':len(model.examples),
        'categories':len(model.codes),
        'trained_ranker_present':getattr(model,'ranker',None) is not None,
        'semantic_enabled':getattr(model,'semantic_enabled',False),
        'model_sha256':hashlib.sha256(Path(a.model).read_bytes()).hexdigest(),
        'network_socket_guard': True, 'keys_removed': True,
        'python': platform.python_version(), 'platform': platform.platform(),
        'thread_env': {k: os.environ.get(k) for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')},
        'icd11_accuracy': None,
        'accuracy_limitation': 'External source has no gold ICD-11 labels. No predictions were treated as labels.',
    }
    Path(a.report).write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    if result['missing_ids'] or result['invalid_codes'] or result['empty_predictions'] or overlap:
        raise SystemExit('Benchmark integrity failure')


if __name__ == '__main__':
    main()
