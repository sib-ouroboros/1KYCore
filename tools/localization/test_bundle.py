import gzip,json,tempfile,unittest
from pathlib import Path
from bundle import pack,extract,sha
import test_localization as fixtures
from localize import analyse,packages
class Bundles(unittest.TestCase):
    def test_determinism_and_integrity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=root/'src';src.mkdir();p=src/'packages';p.mkdir()
            t,s=fixtures.MatchingTests().fixture();_,c,_=analyse(t,s,'fixture',(fixtures.MatchingTests.rule,))
            # Production allowlist fixture uses a real allowed destination name.
            t['page_text_locale']=t.pop('texts_locale');c[0]['table']='page_text_locale'
            m=packages(t,c,p)
            (src/'manifest.json').write_text(json.dumps(m),encoding='utf8')
            (src/'candidates.json').write_text('[]',encoding='utf8');(src/'summary.json').write_bytes(b'{\r\n  "value": 1\r\n}\r\n')
            pack(src,root/'one');pack(src,root/'two')
            self.assertNotIn(b'\r',(root/'one/summary.json').read_bytes())
            self.assertEqual({f.name:f.read_bytes() for f in (root/'one').iterdir()},{f.name:f.read_bytes() for f in (root/'two').iterdir()})
            extract(root/'one',root/'out')
            self.assertEqual((root/'out/demo-001.apply.sql').read_bytes(),(p/'demo-001.apply.sql').read_bytes())
            bad=root/'one/demo-001.apply.sql.gz';bad.write_bytes(b'corrupt')
            with self.assertRaises(ValueError):extract(root/'one',root/'corrupt')
    def test_path_traversal_rejected_before_extract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'catalog.json').write_text(json.dumps({'files_sha256':{'../outside':'bad'}}),encoding='utf8')
            with self.assertRaises(ValueError):extract(root,root/'out')
if __name__=='__main__':unittest.main()
