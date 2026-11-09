import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

class CLITests(unittest.TestCase):
    def test_report_and_overwrite_protection(self):
        root=Path(__file__).resolve().parents[1]
        inputs=['examples/publication-demo.ipynb']
        before=[hashlib.sha256((root/x).read_bytes()).digest() for x in inputs]
        env={**os.environ,'PYTHONPATH':str(root/'src')}
        with tempfile.TemporaryDirectory() as d:
            dest=str(Path(d)/'report.html')
            cmd=[sys.executable,'-m','notebook_publish_check',*inputs,'--output',dest]
            result=subprocess.run(cmd,cwd=root,env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,1,result.stderr)
            self.assertTrue(Path(dest).is_file())
            self.assertEqual(subprocess.run(cmd,cwd=root,env=env,capture_output=True).returncode,2)
            cmd[-1]=inputs[0]
            self.assertEqual(subprocess.run(cmd,cwd=root,env=env,capture_output=True).returncode,2)
        self.assertEqual(before,[hashlib.sha256((root/x).read_bytes()).digest() for x in inputs])
