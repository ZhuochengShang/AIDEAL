"""Canonical registry IDs must never be rendered as executable call syntax."""
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from types import SimpleNamespace
import unittest

ROOT=Path(os.environ.get('AIDEAL_TEST_ROOT',Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(ROOT/'vendor/aideal_engine/src'))
from aideal.prompts import load


class ReadmeEntryPromptTests(unittest.TestCase):
    def test_registry_identity_is_separate_from_callable_access(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            prompt=Path(os.environ.get('AIDEAL_ENTRY_PROMPT',ROOT/'vendor/aideal_engine/src/aideal/default_prompts/aideal/readme_entry.md'))
            custom=root/'prompts/aideal';custom.mkdir(parents=True)
            (custom/'readme_entry.md').write_bytes(prompt.read_bytes())
            cfg=SimpleNamespace(root=root,raw={},project_name='Example',language='Python')
            for identity,access,language,code in [
                ('java:demo.Owner.run','demo.Owner.run','Java','result = instance.run(1);'),
                ('scala:class:demo.Owner.value','demo.Owner.value','Scala','val result = instance.value'),
                ('python:demo.module.run','demo.module.run','Python','result = demo.module.run(1)'),
            ]:
                with self.subTest(identity=identity):
                    _,user=load(cfg,'aideal/readme_entry',language=language,api_name=identity,
                        api_facts=json.dumps({'api_id':identity,'display_name':access.rsplit('.',1)[1],
                            'qualified_name':access,'preferred_public_path':access}),
                        original_readme_context='context',test_examples=code,
                        original_examples='No matching original call.',template=f'## API Test: `{identity}`')
                    self.assertIn(identity,user)
                    self.assertIn(access,user)
                    self.assertNotRegex(user,re.escape(identity)+r'\s*\(')
                    self.assertNotIn('value.'+identity,user)
                    codeblocks=re.findall(r'```(?:Java|Scala|Python)\n(.*?)\n```',user,re.S)
                    self.assertEqual(codeblocks,[code])
                    self.assertNotIn(identity,codeblocks[0])
                    self.assertIn('registry label, not executable syntax',user)
                    self.assertIn('not execution\nvalidation',user)
                    self.assertNotIn('these compile and pass',user)
                    self.assertNotIn('it compiles\n   and passes',user)
                    self.assertNotIn('instance/implicit form',user)


if __name__=='__main__':unittest.main()
