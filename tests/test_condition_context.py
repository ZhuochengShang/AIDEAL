"""Package-qualified bank identities must still retrieve short README headings."""
from pathlib import Path
import tempfile
import unittest

from workflow.condition_context import public_context


class QualifiedDocumentationTests(unittest.TestCase):
    def test_short_method_heading_is_found_after_unrelated_long_sections(self):
        with tempfile.TemporaryDirectory() as directory:
            document = Path(directory) / 'README.md'
            document.write_text('# Library\n' + 'Introduction. ' * 100
                                + '\n## API Test: `numTiles`\nUse metadata.numTiles without parentheses.\n')
            cfg = {'conditions': {'original': {'documents': [str(document)]}},
                   'common': {'documentation_max_characters': 100}}
            case = {'prompt': 'Count tiles.', 'target_apis': ['edu.example.RasterMetadata.numTiles']}
            prompt, receipt = public_context({'config': cfg}, 'original', case)
            self.assertIn('Use metadata.numTiles without parentheses.', prompt)
            self.assertEqual(receipt['documentation']['selected_section_indices'][0], 1)
            self.assertEqual(receipt['documentation']['retrieval_terms'],
                             ['RasterMetadata.numTiles', 'edu.example.RasterMetadata.numTiles', 'numTiles'])
            self.assertTrue(receipt['documentation']['truncated'])


if __name__ == '__main__':
    unittest.main()
