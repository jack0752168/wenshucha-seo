import datetime as dt
import unittest
import funnel_report as report


class ProductFunnel(unittest.TestCase):
    def event(self, eid, surface, path='/', **fields):
        return {'eid': eid, 'sid': eid, 'event': 'cta_search', 'site': 'www',
                'path': path, 'surface': surface, 'source': 'direct',
                'received_at': '2026-11-06T04:00:00Z', **fields}

    def data(self, events, cutoff='2026-11-06T03:00:00Z'):
        return {'meta': {'started_at': '2026-10-12T00:00:00Z',
                         'research_cta_tracking_started_at': cutoff},
                'events': events, 'receipts': []}

    def test_product_destinations_and_five_entry_paths(self):
        paths = ['/', '/pricing/', '/case-search/',
                 '/blog/similar-case-search-completeness-guide.html',
                 '/blog/limitation-period-defense-tolling-search.html']
        events = [self.event(str(i), 'inline', path) for i, path in enumerate(paths)]
        events += [self.event('app', 'report', '/case-research/'),
                   self.event('classic', 'detail'),
                   self.event('mcp', 'mcp', event='cta_mcp')]
        p = report.summarize(self.data(events), dt.date(2026, 11, 6))['products']
        self.assertEqual(p['session_counts'], {'research_intro': 5, 'research_app': 1,
                         'classic_search': 1, 'mcp': 1, 'legacy_or_ambiguous': 0})
        self.assertEqual(set(p['entry_path_sessions']['research_intro']), set(paths))
        self.assertIsNone(p['research_registered_source'])
        self.assertIsNone(p['research_payments'])

    def test_qa_self_bots_and_duplicates_do_not_inflate(self):
        real = self.event('real', 'inline')
        events = [real, real, self.event('qa', 'report', qa=True),
                  self.event('bot', 'inline', bot=True), {**self.event('self', 'detail'), 'self': True}]
        p = report.summarize(self.data(events), dt.date(2026, 11, 6))['products']
        self.assertEqual(p['session_counts']['research_intro'], 1)
        self.assertEqual(p['session_counts']['research_app'], 0)
        self.assertEqual(p['session_counts']['classic_search'], 0)

    def test_legacy_default_and_old_timestamp_stay_ambiguous(self):
        events = [self.event('old', 'inline', received_at='2026-11-06T02:00:00Z'),
                  self.event('cached', 'page'), self.event('tob', 'detail', site='tob')]
        p = report.summarize(self.data(events), dt.date(2026, 11, 6))['products']
        self.assertEqual(p['session_counts']['legacy_or_ambiguous'], 3)
        self.assertEqual(p['session_counts']['research_intro'], 0)

    def test_pre_rollout_is_unknown_not_zero(self):
        p = report.summarize(self.data([]), dt.date(2026, 11, 5))['products']
        self.assertEqual(p['status'], 'unmeasured')
        self.assertIsNone(p['session_counts']['research_intro'])
        p = report.summarize(self.data([], None), dt.date(2026, 11, 6))['products']
        self.assertIsNone(p['session_counts']['research_app'])


if __name__ == '__main__':
    unittest.main()
