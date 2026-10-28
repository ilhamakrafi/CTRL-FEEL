import tempfile
import unittest
from pathlib import Path
from engine import Analyzer, classify_scores, validate_request


class EngineTests(unittest.TestCase):
    def test_invalid_requests(self):
        for data in (None, [], {}, {'user_text': ' '}, {'user_text': 3}, {'user_text':'x'*2001}, {'user_text':'hello','current_system_action':[]}):
            with self.subTest(data=type(data).__name__), self.assertRaises(ValueError):
                validate_request(data)

    def test_threshold_priority_and_boundaries(self):
        self.assertEqual(classify_scores([1,4,4]), 'rejects_help')
        self.assertEqual(classify_scores([2,3,3]), 'stays_negative')
        self.assertEqual(classify_scores([2.5,3.5,3]), 'opens_up')
        for scores in ([1,2], [1,float('nan'),3], [1,2,float('inf')]):
            with self.assertRaises(ValueError):
                classify_scores(scores)

    def test_missing_csv_and_real_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            analyzer = Analyzer(directory)
            self.assertEqual(analyzer.next_action('acknowledge','opens_up'),('ask_clarification','fallback_missing_csv'))
            csv = Path(directory)/'My_Aggregated_Logic.csv'
            csv.write_text('Current_System_Action,User_Reaction,Next_System_Action\nacknowledge,opens_up,offer_help\n',encoding='utf-8')
            self.assertEqual(analyzer.next_action('acknowledge','opens_up'),('offer_help','csv'))
            self.assertEqual(analyzer.next_action('offer_help','opens_up'),('ask_clarification','fallback_no_match'))
            csv.write_text('bad,columns\n1,2\n',encoding='utf-8')
            with self.assertRaises(ValueError):
                analyzer.next_action('acknowledge','opens_up')

    def test_result_contract_without_loading_model(self):
        with tempfile.TemporaryDirectory() as directory:
            analyzer = Analyzer(directory)
            analyzer.scores = lambda _: [3.2,3.0,2.8]
            result = analyzer.analyze({'user_text':'Hello'})
            self.assertEqual(result['vad_scores']['valence'],3.2)
            self.assertEqual(result['next_system_action'],'ask_clarification')
            self.assertEqual(result['decision_source'],'fallback_missing_csv')


if __name__ == '__main__':
    unittest.main()
