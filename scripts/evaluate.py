"""Keep resubstitution, title-only and genuinely held-out scores separate."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sklearn.model_selection import KFold
from coder.engine import OfflineCoder, rows


def metrics(gold, predictions):
    one = sum(p[0] in r['gold'] for r, p in zip(gold, predictions))
    three = sum(bool(set(p) & set(r['gold'])) for r, p in zip(gold, predictions))
    n = len(gold)
    return {'n': n, 'top1_hits': one, 'top3_hits': three,
            'top1_accuracy': round(one/n, 4), 'top3_accuracy': round(three/n, 4),
            'score_out_of_75': round(75*(2/3*one/n+1/3*three/n), 3)}


def write_predictions(path, notes, predictions):
    with open(path, 'w') as f:
        for r, p in zip(notes, predictions):
            f.write(json.dumps({'id': r['id'], 'codes': p})+'\n')


def main():
    start = time.perf_counter()
    categories = json.loads(Path('data/mms-2026-01.json').read_text())
    notes = rows('data/dev_notes.jsonl')
    titles_only = OfflineCoder(categories, [])
    title_pred = [titles_only.predict(r['text'])[0] for r in notes]
    del titles_only
    full = OfflineCoder.load('artifacts/offline.joblib')
    resub = [full.predict(r['text'])[0] for r in notes]
    profile={'ranker':full.ranker_kind,'learned_primary':full.learned_primary,'who_enrichment':full.reference is not None}
    del full
    heldout = [None]*len(notes)
    diagnostics = [None]*len(notes)
    fold_reports = []
    for fold, (train, test) in enumerate(KFold(n_splits=5, shuffle=True, random_state=20261105).split(notes), 1):
        model = OfflineCoder(categories, [notes[int(i)] for i in train])
        assert not {notes[int(i)]['id'] for i in test} & set(model.example_ids)
        for i in test:
            heldout[int(i)], diagnostic = model.predict(notes[int(i)]['text'])
            diagnostics[int(i)] = {'id': notes[int(i)]['id'], 'gold':notes[int(i)]['gold'],
                                   'pred':heldout[int(i)], 'fold':fold, **diagnostic}
        fold_reports.append({'fold': fold, 'training_ids': model.example_ids,
                             'heldout_ids': [notes[int(i)]['id'] for i in test]})
        print(f'Finished held-out fold {fold}/5', flush=True)
        del model
    for name, predictions in [('titles-only',title_pred), ('resubstitution',resub), ('heldout',heldout)]:
        write_predictions(f'reports/{name}-predictions.jsonl', notes, predictions)
    result = {
        'title_only_no_supervised_examples': metrics(notes,title_pred),
        'training_set_resubstitution_not_generalisation': metrics(notes,resub),
        'five_fold_out_of_fold': metrics(notes,heldout),
        'candidate_recall_top50': round(sum(bool(set(r['gold']) & set(d['candidate_codes_top50'])) for r,d in zip(notes,diagnostics))/len(notes),4),
        'candidate_recall_top100': round(sum(bool(set(r['gold']) & set(d['candidate_codes_top100'])) for r,d in zip(notes,diagnostics))/len(notes),4),
        'trained_method': profile,
        'semantic_retrieval_active': any(d['semantic_retrieval'] for d in diagnostics),
        'folds': fold_reports, 'seed': 20261105,
        'seconds': round(time.perf_counter()-start, 3),
        'limitations': [
            'Only 60 development notes; wide uncertainty and narrow chapter coverage.',
            'Each fold fits vocabulary and supervised examples without the held-out notes.',
            'Handwritten normalisation and assessment extraction were developed after inspecting dev data; this is not an untouched external accuracy test.',
            'External MTS-Dialog data was not used for fitting or parameter tuning.',
            'No defensible hidden-score estimate from this sample alone.',
        ],
    }
    Path('reports/evaluation.json').write_text(json.dumps(result,indent=2)+'\n')
    Path('reports/heldout-diagnostics.jsonl').write_text('\n'.join(json.dumps(d,ensure_ascii=False) for d in diagnostics)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'folds'},indent=2))


if __name__ == '__main__':
    main()
