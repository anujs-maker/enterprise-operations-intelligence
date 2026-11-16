import unittest, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'scripts')); import run_pipeline
class TestPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.req,cls.c,cls.e,cls.i=run_pipeline.generate(); cls.a=run_pipeline.analyse(cls.req)
    def test_referential_integrity(self):
        cs={x['customer_id'] for x in self.c}; es={x['employee_id'] for x in self.e}; self.assertTrue(all(r['customer_id'] in cs and r['employee_id'] in es for r in self.req))
    def test_sla_range(self): self.assertGreaterEqual(self.a['kpis']['sla_compliance_pct'],0); self.assertLessEqual(self.a['kpis']['sla_compliance_pct'],100)
    def test_reproducibility(self): self.assertEqual(self.req[0]['request_id'],'R000001'); self.assertEqual(len(self.req),500000)
    def test_costs(self): self.assertGreater(self.a['kpis']['operating_cost_inr'],0)
    def test_open_logic(self): self.assertTrue(all((r['status']=='Open' and r['closed_at']=='') or (r['status']=='Closed' and r['closed_at']) for r in self.req))
    def test_open_age(self): self.assertTrue(all(r['open_age_hours']==0 or r['status']=='Open' for r in self.req))
