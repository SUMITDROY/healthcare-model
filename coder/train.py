import argparse
import json
import time
from pathlib import Path

from coder.engine import OfflineCoder, rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--mms', default='data/mms-2026-01.json')
    p.add_argument('--examples', default='data/dev_notes.jsonl')
    p.add_argument('--output', default='artifacts/offline.joblib')
    a = p.parse_args()
    start = time.perf_counter()
    model = OfflineCoder(json.loads(Path(a.mms).read_text()), rows(a.examples))
    model.save(a.output)
    print(json.dumps({'categories': len(model.codes), 'labeled_training_examples': len(model.examples),
                      'seconds': round(time.perf_counter()-start, 3), 'artifact': a.output}))


if __name__ == '__main__':
    main()
