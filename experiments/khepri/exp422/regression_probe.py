"""Minimal independent regression probe for experiment 422 (stdlib only)."""
import sqlite3
import unittest

BASE = '''
CREATE TABLE heads(path TEXT PRIMARY KEY,revision INTEGER NOT NULL,present INTEGER,content BLOB);
CREATE TRIGGER bump AFTER UPDATE OF content,present ON heads WHEN NEW.revision=OLD.revision
BEGIN UPDATE heads SET revision=revision+1 WHERE path=NEW.path; END;
CREATE TRIGGER no_delete BEFORE DELETE ON heads
BEGIN SELECT RAISE(ABORT,'no physical delete'); END;
CREATE TRIGGER no_regression BEFORE UPDATE OF revision ON heads WHEN NEW.revision<=OLD.revision
BEGIN SELECT RAISE(ABORT,'no revision regression'); END;
'''
HARDEN = '''
CREATE TABLE seen_paths(path TEXT PRIMARY KEY);
CREATE TRIGGER reject_reinsert BEFORE INSERT ON heads
WHEN EXISTS(SELECT 1 FROM seen_paths WHERE path=NEW.path)
BEGIN SELECT RAISE(ABORT,'reinsert forbidden'); END;
CREATE TRIGGER track_path AFTER INSERT ON heads
BEGIN INSERT OR IGNORE INTO seen_paths(path) VALUES(NEW.path); END;
CREATE TRIGGER reject_rename BEFORE UPDATE OF path ON heads WHEN NEW.path!=OLD.path
BEGIN SELECT RAISE(ABORT,'rename forbidden'); END;
'''

def db(hardened=False):
    con=sqlite3.connect(':memory:')
    con.execute('PRAGMA recursive_triggers=OFF')
    con.executescript(BASE + (HARDEN if hardened else ''))
    con.execute('INSERT INTO heads VALUES (?,1,1,?)',('seo/a',b'original'))
    return con

class MutationProbe(unittest.TestCase):
    def test_replace_resets_revision_in_baseline(self):
        with db() as con:
            con.execute('INSERT OR REPLACE INTO heads VALUES (?,1,1,?)',('seo/a',b'peer'))
            self.assertEqual(con.execute('SELECT revision,content FROM heads').fetchone(),(1,b'peer'))

    def test_rename_and_recreate_resets_revision_in_baseline(self):
        with db() as con:
            con.execute("UPDATE heads SET path='seo/elsewhere' WHERE path='seo/a'")
            con.execute('INSERT INTO heads VALUES (?,1,1,?)',('seo/a',b'peer'))
            self.assertEqual(con.execute("SELECT revision,content FROM heads WHERE path='seo/a'").fetchone(),(1,b'peer'))

    def test_hardened_rejects_replace(self):
        with db(True) as con:
            with self.assertRaises(sqlite3.IntegrityError):
                con.execute('INSERT OR REPLACE INTO heads VALUES (?,1,1,?)',('seo/a',b'peer'))

    def test_hardened_rejects_rename(self):
        with db(True) as con:
            with self.assertRaises(sqlite3.IntegrityError):
                con.execute("UPDATE heads SET path='seo/elsewhere' WHERE path='seo/a'")

    def test_legacy_upsert_is_incompatible_with_hardening(self):
        with db(True) as con:
            with self.assertRaises(sqlite3.IntegrityError):
                con.execute('''INSERT INTO heads VALUES (?,1,1,?)
                    ON CONFLICT(path) DO UPDATE SET revision=revision+1,content=excluded.content''',('seo/a',b'peer'))

if __name__=='__main__': unittest.main()
