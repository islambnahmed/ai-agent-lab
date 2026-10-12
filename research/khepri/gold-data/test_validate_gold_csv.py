import csv, datetime as dt, os, tempfile, unittest
from validate_gold_csv import validate, REQUIRED
class GoldValidationTests(unittest.TestCase):
    def check(self, edits=None, error=False):
        rows=[["2025-01-02","2650","demo","XAUUSD","USD","troy_ounce","2025-01-02T22:00:00Z"],
              ["2025-01-03","2660","demo","XAUUSD","USD","troy_ounce","2025-01-03T22:00:00Z"]]
        if edits: edits(rows)
        with tempfile.NamedTemporaryFile(mode="w",newline="",suffix=".csv",delete=False) as f:
            p=f.name;w=csv.writer(f);w.writerow(REQUIRED);w.writerows(rows)
        try:
            if error:
                with self.assertRaises(ValueError): validate(p)
            else: self.assertEqual(len(validate(p)),2)
        finally: os.unlink(p)
    def test_valid(self): self.check()
    def test_duplicate_date(self): self.check(lambda r:r[1].__setitem__(0,r[0][0]),True)
    def test_reversed(self): self.check(lambda r:r.reverse(),True)
    def test_negative(self): self.check(lambda r:r[0].__setitem__(1,"-1"),True)
    def test_nan(self): self.check(lambda r:r[0].__setitem__(1,"nan"),True)
    def test_mixed_asset(self): self.check(lambda r:r[1].__setitem__(3,"GC"),True)
    def test_naive_timestamp(self): self.check(lambda r:r[1].__setitem__(6,"2025-01-03T22:00:00"),True)
    def test_future_session(self): self.check(lambda r:r[1].__setitem__(6,"2025-01-02T22:00:00Z"),True)
if __name__=="__main__": unittest.main()
