import csv
from datetime import date, timedelta
from pathlib import Path
import tempfile
import unittest
from temporal_overlap import read_csv
from omission_robustness import probe
from block_omission import evaluate, main


def make_csv(path, rows):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['date','query','page','clicks','impressions','position'])
        for d, q, p, n in rows:
            w.writerow([d,q,p,0,n,8])


def overlap(days=5):
    rows=[]
    for i in range(days):
        d=(date(2026,9,1)+timedelta(days=i)).isoformat()
        rows.extend([(d,'gold query','https://example.test/a',40),
                     (d,'gold query','https://example.test/b',30)])
    return rows


class BlockOmissionTests(unittest.TestCase):
    def test_single_row_stable_but_missing_page_erases_signal(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'gsc.csv'
            make_csv(p, overlap())
            grouped=read_csv(p)
            single=probe(grouped)['queries'][0]
            self.assertTrue(single['stable_under_any_single_row_omission'])
            blocks=evaluate(grouped)['queries'][0]
            self.assertEqual(blocks['baseline'],'persistent_co_visibility')
            self.assertEqual(blocks['blocks']['one_page']['changed'],2)
            self.assertEqual(blocks['blocks']['one_page']['outcomes'],{'not_detected':2})
            self.assertEqual(blocks['blocks']['one_date']['changed'],0)
            self.assertEqual(blocks['blocks']['calendar_window']['changed'],3)

    def test_gap_aware_calendar_window(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'gsc.csv'
            rows=overlap(2)
            rows.extend([('2026-09-10','gold query','https://example.test/a',40),
                         ('2026-09-10','gold query','https://example.test/b',30)])
            make_csv(p,rows)
            out=evaluate(read_csv(p),window_days=3)['queries'][0]
            self.assertEqual(out['blocks']['calendar_window']['probes'],3)
            self.assertEqual(out['blocks']['calendar_window']['examples'][0]['removed_rows'],4)

    def test_budget_marks_unassessed(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'gsc.csv';make_csv(p,overlap())
            x=evaluate(read_csv(p),max_probes_total=2)['queries'][0]
            self.assertEqual(x['status'],'not_assessed_budget')
            self.assertNotIn('blocks',x)

    def test_empty_and_invalid_params(self):
        self.assertEqual(evaluate({})['assessed_queries'],0)
        for opts in ({'window_days':1},{'window_days':2.5},{'max_probes_per_query':0},
                     {'max_probes_total':0}):
            with self.assertRaises(ValueError): evaluate({},**opts)

    def test_cli(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'gsc.csv';make_csv(p,overlap())
            self.assertEqual(main([str(p),'--window-days','3']),0)
            self.assertEqual(main([str(p),'--window-days','1']),2)

if __name__ == '__main__': unittest.main()
