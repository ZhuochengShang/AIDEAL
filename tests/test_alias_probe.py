"""Offline tests: synthetic source/evidence only; no compiler, library or provider."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
if SCRIPTS.is_dir(): sys.path.insert(0, str(SCRIPTS))

from alias_forwarders import (GEOLITE, ReviewRequired, alias_call, canonical_signature,
                              certify, parse_module)
from alias_development_cases import program
from alias_probe import inspect_proposal, new_output
from alias_probe_evidence import bind, save, verified
from alias_probe_execution import compare, observations, command


def target(method='readType', owner='Feature', descriptor='(Ljava/io/ObjectInput;)Lorg/apache/spark/sql/types/DataType;', instance=False):
    return {'api':GEOLITE+'.'+owner+'.'+method,'owner':owner,'method':method,
            'jvm_owner':GEOLITE+'.'+owner+('' if instance else '$'),'descriptor':descriptor}


def module(definition):
    return parse_module('package '+GEOLITE+'\nimport java.io._\nimport org.apache.spark.sql.types._\n'
                        'import org.apache.spark.sql.Row\nimport java.awt.geom.Point2D\n'
                        'import org.locationtech.jts.geom.Envelope\nobject FriendlyAliases { '+definition+' }')


def certified(definition, t=None, parameters=None, parentheses=True):
    m=module(definition)
    return certify(m,m['methods'][0],t or target(),
                   parameters if parameters is not None else [{'name':'in','type':'ObjectInput','default':None}],parentheses)


class ForwardingTests(unittest.TestCase):
    def test_static_exact_forwarding(self):
        cert=certified('def decodeType(in: ObjectInput): DataType = Feature.readType(in)')
        self.assertEqual(cert['canonical_event'],GEOLITE+'.Feature$.readType(Ljava/io/ObjectInput;)Lorg/apache/spark/sql/types/DataType;')
        self.assertEqual(alias_call(cert,['stream']),GEOLITE+'.FriendlyAliases.decodeType(stream)')

    def test_instance_parameter_permutation_is_explicit(self):
        cert=certified('def resized(height: Int, m: RasterMetadata, width: Int): RasterMetadata = m.rescale(width,height)',
             target('rescale','RasterMetadata','(II)L'+GEOLITE.replace('.','/')+'/RasterMetadata;',True),
             [{'name':'width','default':None},{'name':'height','default':None}])
        self.assertEqual(alias_call(cert,['w','h'],'metadata'),GEOLITE+'.FriendlyAliases.resized(h, metadata, w)')

    def test_property_and_null_defaults(self):
        t=target('numTiles','RasterMetadata','()I',True)
        cert=certified('def tileCount(m: RasterMetadata): Int = m.numTiles',t,[],False)
        self.assertEqual(alias_call(cert,[],'r'),GEOLITE+'.FriendlyAliases.tileCount(r)')
        with self.assertRaises(ReviewRequired): certified('def tileCount(m: RasterMetadata): Int = m.numTiles()',t,[],False)
        text='def append(f: IFeature, value: Any, name: String = null, kind: DataType = null): IFeature = {'
        signature=canonical_signature(text,1,'append')
        self.assertEqual([p['default'] for p in signature['parameters']],[None,None,'null','null'])
        self.assertTrue(signature['parentheses'])

    def test_parenthesized_single_expression_block(self):
        certified('def decodeType(in: ObjectInput): DataType = { Feature.readType(in) }')

    def test_comments_are_lexical_only(self):
        certified('/* def bad() = sideEffect() */ def decodeType(in: ObjectInput): DataType = /* nested /* x */ */ Feature.readType(in)')

    def test_rejects_effects_initializers_and_unsupported_constructs(self):
        invalid=[
            'val side = println("x"); def decodeType(in: ObjectInput): DataType = Feature.readType(in)',
            'def decodeType(in: ObjectInput): DataType = { println(in); Feature.readType(in) }',
            'def decodeType(in: ObjectInput): DataType = Feature.readType(transform(in))',
            'def decodeType(in: ObjectInput): DataType = Feature.readType(null)',
            'def decodeType(in: ObjectInput): DataType = { val x=in; Feature.readType(x) }',
            '@deprecated def decodeType(in: ObjectInput): DataType = Feature.readType(in)',
            'def decodeType[A](in: ObjectInput): DataType = Feature.readType(in)',
            'def decodeType(in: => ObjectInput): DataType = Feature.readType(in)',
            'def decodeType(in: ObjectInput)(implicit x: Int): DataType = Feature.readType(in)',
            'def decodeType(in: ObjectInput): DataType = Feature.readType(in); object Extra {}',
            'def Feature(in: ObjectInput): DataType = Feature.readType(in)',
        ]
        for text in invalid:
            with self.subTest(text=text),self.assertRaises(ReviewRequired): module(text)

    def test_rejects_wrong_owner_type_return_and_extra_argument(self):
        for text in [
            'def decodeType(in: ObjectInput): DataType = RasterSchemaHelper.readType(in)',
            'def decodeType(in: ObjectOutput): DataType = Feature.readType(in)',
            'def decodeType(in: ObjectInput): StructType = Feature.readType(in)',
            'def decodeType(in: ObjectInput, extra: Int): DataType = Feature.readType(in)',
            'def decodeType(in: ObjectInput): DataType = Feature.readType(in,in)',
        ]:
            with self.subTest(text=text),self.assertRaises(ReviewRequired): certified(text)

    def test_rejects_receiver_and_default_mismatch(self):
        with self.assertRaises(ReviewRequired): certified('def decodeType(in: ObjectInput = null): DataType = Feature.readType(in)')
        t=target('numTiles','RasterMetadata','()I',True)
        with self.assertRaises(ReviewRequired): certified('def tileCount(m: IFeature): Int = m.numTiles',t,[],False)

    def test_rejects_import_aliases_and_builtin_shadow(self):
        for imports in ['java.io.{ObjectInput => Input}','some.package._','java.awt.geom.Point2D.Double']:
            text='package '+GEOLITE+'\nimport '+imports+'\nobject Friendly { def one(): Int = x.numTiles }'
            with self.subTest(imports=imports),self.assertRaises(ReviewRequired): parse_module(text)

    def test_rejects_second_object_and_duplicate_definition(self):
        with self.assertRaises(ReviewRequired): parse_module('package x\nobject A { def x(): Int = a.b } object B {}')
        with self.assertRaises(ReviewRequired): module('def x(in: ObjectInput): DataType = Feature.readType(in)\ndef x(in: ObjectInput): DataType = Feature.readType(in)')

    def test_source_header_exact_line_and_property(self):
        self.assertEqual(canonical_signature('def numTiles: Int = numTilesX * numTilesY',1,'numTiles'),
                         {'parameters':[],'parentheses':False,'returns':'Int'})
        with self.assertRaises(ReviewRequired): canonical_signature('// def numTiles: Int = 1\ndef other = 2',1,'numTiles')

    def test_generated_program_has_fresh_inputs_and_no_bank(self):
        cert=certified('def decodeType(in: ObjectInput): DataType = Feature.readType(in)')
        text,count=program(cert)
        self.assertEqual(count,4)
        self.assertIn('new ObjectInputStream(new ByteArrayInputStream',text)
        self.assertIn('if (useAlias)',text)
        self.assertIn('AIDEAL_DEVELOPMENT_PROBE={\\"mode\\":',text)
        self.assertNotIn('StudySupport',text)
        self.assertNotIn('reference.scala',text)

    def test_whole_proposal_rejects_unlisted_extra_method(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); code=root/'aliases.scala'
            code.write_text('package '+GEOLITE+'\nimport java.io.ObjectInput\nimport org.apache.spark.sql.types.DataType\nobject A { def decodeType(in: ObjectInput): DataType = Feature.readType(in) }')
            proposal={'baseline_revision':'a'*40,'aliases':[], 'artifacts':{'alias':{**bind(code),'target':'src/'+GEOLITE.replace('.','/')+'/A.scala'}}}
            path=root/'proposal.json';save(path,proposal)
            with mock.patch('alias_probe.git',side_effect=['a'*40,'README.md']),self.assertRaises(ReviewRequired):
                inspect_proposal(path,{},root)


class EvidenceTests(unittest.TestCase):
    def setUp(self): self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
    def tearDown(self): self.temp.cleanup()
    def put(self,name,text):
        p=self.root/name;p.write_text(text);return bind(p)
    def run_files(self,mode,obs=None):
        obs=obs or ['ok:23','exception:java.io.EOFException']
        c='p.Target$.call(I)I';a='p.Aliases$.friendly(I)I';overlay=self.root/'overlay.jar'
        return {'process':self.put(mode+'.process',json.dumps({'returncode':0})),
          'stdout':self.put(mode+'.stdout','AIDEAL_DEVELOPMENT_PROBE='+json.dumps({'mode':mode,'observations':obs})+'\n'),
          'stderr':self.put(mode+'.stderr',''),
          'trace':self.put(mode+'.trace',c+'\n'+(a+'\n' if mode=='alias' else '')),
          'classload':self.put(mode+'.classes','[0.1s][info][class,load] p.Target$ source: '+overlay.as_uri()+'\n'+
                              ('[0.1s][info][class,load] p.Aliases$ source: '+overlay.as_uri()+'\n' if mode=='alias' else ''))}
    def entry(self):return {'canonical_event':'p.Target$.call(I)I','alias_event':'p.Aliases$.friendly(I)I','example_count':2}
    def test_separate_trace_and_equal_observations(self):
        c,a=self.run_files('canonical'),self.run_files('alias')
        self.assertTrue(compare(c,a,self.entry(),self.root/'overlay.jar')['observations_equal'])
    def test_mismatched_observations_fail(self):
        c,a=self.run_files('canonical'),self.run_files('alias',['ok:99','ok:4'])
        with self.assertRaises(ValueError):compare(c,a,self.entry(),self.root/'overlay.jar')
    def test_reference_trace_cannot_supply_missing_alias_target(self):
        c,a=self.run_files('canonical'),self.run_files('alias')
        a['trace']=self.put('alias.trace','p.Aliases$.friendly(I)I\n')
        with self.assertRaises(ValueError):compare(c,a,self.entry(),self.root/'overlay.jar')
    def test_missing_alias_event_fails(self):
        c,a=self.run_files('canonical'),self.run_files('alias')
        a['trace']=self.put('alias.trace','p.Target$.call(I)I\n')
        with self.assertRaises(ValueError):compare(c,a,self.entry(),self.root/'overlay.jar')
    def test_wrong_class_origin_fails(self):
        c,a=self.run_files('canonical'),self.run_files('alias')
        a['classload']=self.put('alias.classes','[info][class,load] p.Aliases$ source: file:/wrong.jar\n')
        with self.assertRaises(ValueError):compare(c,a,self.entry(),self.root/'overlay.jar')
    def test_all_exception_pairs_do_not_pass(self):
        c=self.run_files('canonical',['exception:Bad','exception:Bad'])
        with self.assertRaises(ValueError):observations(c['stdout']['path'],'canonical')
    def test_duplicate_or_missing_marker_fails(self):
        c=self.run_files('canonical');path=Path(c['stdout']['path']);text=path.read_text();path.write_text(text+text)
        with self.assertRaises(ValueError):observations(path,'canonical')
        path.write_text('')
        with self.assertRaises(ValueError):observations(path,'canonical')
    def test_changed_or_deleted_raw_evidence_fails(self):
        ref=self.put('bound','before');Path(ref['path']).write_text('after')
        with self.assertRaises(ValueError):verified(ref)
        Path(ref['path']).unlink()
        with self.assertRaises((ValueError,FileNotFoundError)):verified(ref)
    def test_immutable_output_and_source_separation(self):
        p=self.root/'receipt.json';save(p,{'value':1})
        with self.assertRaises(FileExistsError):save(p,{'value':2})
        self.assertEqual(json.loads(p.read_text()),{'value':1})
        with self.assertRaises(ValueError):new_output(self.root/'inside',[self.root])
    def test_launch_failure_retains_process_evidence(self):
        with mock.patch('alias_probe_execution.subprocess.Popen',side_effect=OSError('synthetic launch failure')):
            with self.assertRaises(ValueError):command(['nonexistent'],self.root,'attempt')
        record=json.loads((self.root/'attempt.process.json').read_text())
        self.assertIsNone(record['returncode']);self.assertIn('launch_error',record)
        self.assertTrue((self.root/'attempt.stderr').exists())


if __name__=='__main__': unittest.main()
