"""Exercise the real planner with fictional manifests and no writes."""
import argparse
import copy
import itertools
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import plan_review_scope as scope


class ScopeUnionTests(unittest.TestCase):
    def plan(self, layers):
        before = {'schema_version': 1, 'manifest_id': 'fictional-before',
                  'layers': {k: {'fixture': {'sha256': 'a'}} for k in scope.LAYERS},
                  'reviews': {r: {'verdict': 'PASS'} for r in scope.ROLES}}
        after = copy.deepcopy(before); after['manifest_id'] = 'fictional-after'
        for layer in layers:
            after['layers'][layer]['fixture']['sha256'] = 'b'
        result = {}
        with patch.object(scope, 'load_json', side_effect=[before, after]), patch.object(scope, 'write_json', side_effect=lambda _, data: result.update(data)), patch('builtins.print'):
            scope.command_plan(argparse.Namespace(before='before', after='after', output='unused'))
        return result

    def test_every_combination_retains_all_single_layer_checks(self):
        singles = {layer: set(self.plan([layer])['required_checks']) for layer in scope.LAYERS}
        for size in range(1, len(scope.LAYERS)+1):
            for layers in itertools.combinations(scope.LAYERS, size):
                with self.subTest(layers=layers):
                    plan = self.plan(layers)
                    required = set(plan['required_checks'])
                    self.assertTrue(set.union(*(singles[layer] for layer in layers)) <= required)
                    self.assertEqual(len(required), len(plan['required_checks']))

    def test_visual_plus_layout_cannot_drop_geometry(self):
        plan = self.plan(['visual', 'layout_desktop', 'layout_mobile'])
        self.assertTrue({'desktop_geometry', 'mobile_geometry', 'desktop_visual_review', 'mobile_visual_review'} <= set(plan['required_checks']))
        self.assertEqual(set(plan['required_reviews']), {'reader', 'visual'})
        self.assertEqual(plan['reused_reviews'], ['source'])

    def test_content_change_cannot_reuse_source_review(self):
        plan = self.plan(['content', 'layout_desktop'])
        self.assertEqual(set(plan['required_reviews']), set(scope.ROLES))
        self.assertEqual(plan['reused_reviews'], [])

    def test_publishing_only_does_not_add_rendering_checks(self):
        self.assertEqual(self.plan([])['required_checks'], ['live_target_verification'])


if __name__ == '__main__':
    unittest.main()
