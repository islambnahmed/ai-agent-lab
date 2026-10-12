import datetime as dt
import unittest
from collect_research import parse_bars, parse_vintages, DownloadForm

class SourceTests(unittest.TestCase):
    def setUp(self): self.asof=dt.datetime(2026,1,2,tzinfo=dt.timezone.utc)
    def test_fixed_est_to_utc_and_no_fill(self):
        raw=b'20250701 190000;3000;3010;2990;3005;0\n20250701 190200;3005;3010;2990;3007;0\n'
        rows,audit=parse_bars(raw,'2025',self.asof)
        self.assertEqual(rows[0]['date'],'2025-07-02')
        self.assertEqual(rows[0]['observedMinutes'],2)
        self.assertEqual(rows[0]['price'],3007)
        self.assertEqual(audit['maxGapMinutes'],2)
    def test_rejects_bad_bars(self):
        for raw in [b'20250701 190000;3000;2990;2990;3005;0\n',
                    b'20250701 190000;3000;3010;2990;NaN;0\n',
                    b'20250701 190000;3000;3010;2990;3005;20\n',
                    b'20260101 190000;3000;3010;2990;3005;0\n']:
            with self.subTest(raw=raw), self.assertRaises(ValueError):parse_bars(raw,'2025',self.asof)
    def test_duplicate_minute_rejected(self):
        raw=b'20250701 190000;3000;3010;2990;3005;0\n'
        with self.assertRaises(ValueError):parse_bars(raw+raw,'2025',self.asof)
    def test_conflicting_minute_quarantines_entire_day(self):
        raw=b'20251026 195900;3000;3010;2990;3005;0\n20251026 190000;3000;3010;2990;3007;0\n20251027 190000;3000;3010;2990;3008;0\n'
        rows,audit=parse_bars(raw,'2025',self.asof,quarantine_conflicting_days=True)
        self.assertEqual([r['date'] for r in rows],['2025-10-28'])
        self.assertEqual(audit['quarantinedUtcDays'],['2025-10-27'])
    def test_bls_dst_and_fetch_time(self):
        from fetch_calendar import parse_ics
        raw=b'BEGIN:VCALENDAR\nBEGIN:VEVENT\nDTSTART;TZID=US-Eastern:20260714T083000\nSUMMARY:Consumer Price Index\nEND:VEVENT\nBEGIN:VEVENT\nDTSTART;TZID=US-Eastern:20260114T083000\nSUMMARY:Consumer Price Index\nEND:VEVENT\nEND:VCALENDAR\n'
        rows=parse_ics(raw,'2026-10-12T18:00:00Z')
        self.assertEqual(rows[0]['scheduledAt'],'2026-01-14T13:30:00Z')
        self.assertEqual(rows[1]['scheduledAt'],'2026-07-14T12:30:00Z')
        self.assertEqual(rows[0]['knownAt'],'2026-10-12T18:00:00Z')
    def test_vintage_cutoff_missing_and_revision(self):
        raw=b'observation_date,DFII10_20240101,DFII10_20250101\n2023-12-28,1.68,1.69\n2024-12-30,,2.1\n'
        rows,counts=parse_vintages(raw,'DFII10',['2024-01-01','2025-01-01'],'2000-01-01')
        self.assertEqual([r['value'] for r in rows],[1.68,2.1])
        self.assertEqual(rows[0]['availableAt'],'2024-01-01T23:59:59.999Z')
        self.assertEqual(counts['2024-01-01'],1)
    def test_wrong_vintage_header_rejected(self):
        with self.assertRaises(ValueError):parse_vintages(b'observation_date,DFII10\n2023-12-28,1.68\n','DFII10',['2024-01-01'],'2000-01-01')
    def test_future_vintage_observation_rejected(self):
        with self.assertRaises(ValueError):parse_vintages(b'observation_date,DFII10_20240101\n2024-01-02,1.68\n','DFII10',['2024-01-01'],'2000-01-01')
    def test_cpi_yoy_uses_same_vintage(self):
        raw=b'observation_date,CPIAUCSL_20240101,CPIAUCSL_20250101\n2022-11-01,100,110\n2023-11-01,105,121\n'
        rows,_=parse_vintages(raw,'CPIAUCSL',['2024-01-01','2025-01-01'],'2000-01-01')
        derived=[r['value'] for r in rows if r['feature']=='us_cpi_yoy_pct']
        self.assertAlmostEqual(derived[0],5);self.assertAlmostEqual(derived[1],10)
    def test_only_reads_requested_download_form(self):
        form=DownloadForm();form.feed('<form id="file_down"><input name="fxpair" value="XAUUSD"></form><form><input name="fxpair" value="EURUSD"></form>')
        self.assertEqual(form.fields,{'fxpair':'XAUUSD'})

if __name__=='__main__': unittest.main()
