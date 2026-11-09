import copy
import unittest
from notebook_publish_check.core import scan,sanitize
from notebook_publish_check.cli import report

def notebook():
 return {'nbformat':4,'nbformat_minor':5,'metadata':{},'cells':[{'cell_type':'code','metadata':{'path':'/Users/demo/a'},'source':'password = "NOT_REAL_SECRET_123"','execution_count':3,'outputs':[{'output_type':'stream','text':['api_key = ','DEMO_ONLY_12345\n','/home/demo/data']}]}]}
class NotebookTests(unittest.TestCase):
 def test_secrets_in_source_and_outputs(self):
  fs=scan(notebook());self.assertEqual({f['area'] for f in fs if f['rule']=='possible-secret'},{'source','outputs'})
  self.assertNotIn('DEMO_ONLY_12345',str(fs))
 def test_does_not_modify_original(self):
  nb=notebook();before=copy.deepcopy(nb);scan(nb);out=sanitize(nb,[0],[0]);self.assertEqual(nb,before);self.assertEqual(out['cells'][0]['outputs'],[]);self.assertIsNone(out['cells'][0]['execution_count']);self.assertEqual(out['cells'][0]['source'],before['cells'][0]['source'])
 def test_source_findings_survive_removal(self):
  fs=scan(sanitize(notebook(),[0],[0]));self.assertTrue(any(f['area']=='source' for f in fs));self.assertFalse(any(f['area']=='outputs' for f in fs))
 def test_rich_output_and_size(self):
  nb=notebook();nb['cells'][0]['outputs']=[{'data':{'image/png':'x'*100,'text/html':'<script>alert(1)</script>'}}]
  rules={f['rule'] for f in scan(nb,50)};self.assertTrue({'large-output','manual-media-review'}<=rules)
 def test_report_cannot_inject_script(self):
  nb=notebook();nb['cells'][0]['source']='</script><script>alert(42)</script>'
  self.assertNotIn('</script><script>alert(42)',report(nb,scan(nb)))
 def test_validation(self):
  with self.assertRaises(ValueError):scan({'nbformat':3})
  with self.assertRaises(ValueError):sanitize(notebook(),[-1])
  with self.assertRaises(ValueError):scan(notebook(),0)
if __name__=='__main__':unittest.main()
