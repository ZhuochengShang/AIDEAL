import unittest
from workflow.scala_owners import owner_at_line


class ScalaOwnersTest(unittest.TestCase):
    def test_companion_class_and_object(self):
        source = 'class A(x: Int) extends B {\n def size = 1\n}\nobject A {\n def size = 2\n}'
        self.assertEqual(owner_at_line(source, 2, 'size')['owner_kind'], 'class')
        self.assertEqual(owner_at_line(source, 5, 'size')['owner_kind'], 'object')

    def test_nested_owner_returns_to_outer(self):
        source = 'object A {\n class B {\n def f = 1\n }\n def g = 2\n}'
        self.assertEqual(owner_at_line(source, 3)['owner_path'], 'A.B')
        self.assertEqual(owner_at_line(source, 5)['owner_path'], 'A')

    def test_comments_literals_and_anonymous_blocks(self):
        source = 'object A {\n /* object Wrong { /* nested } */ } */\n val text = "object Bad { }"\n val raw = """def fake {\n }"""\n def f = List(1).map { x => x }\n}'
        self.assertEqual(owner_at_line(source, 6)['receiver'], 'A')
        with self.assertRaises(ValueError):
            owner_at_line(source, 4, 'fake')

    def test_bodyless_nested_declaration(self):
        source = 'object A {\n case class Item(x: Int)\n def f = 1\n}'
        self.assertEqual(owner_at_line(source, 3)['receiver'], 'A')

    def test_extra_quote_before_triple_close(self):
        source = 'object A {\n val text = """a quoted end""""\n def f = 1\n}'
        self.assertEqual(owner_at_line(source, 3)['receiver'], 'A')

    def test_method_local_definition_is_not_outer_receiver_member(self):
        # RDPro IntermediateVectorTile.reverse (line154) has this nesting.
        source = 'class IntermediateVectorTile {\n def polygon = {\n def reverse(): Unit = { }\n }\n def next = 1\n}'
        with self.assertRaises(ValueError):
            owner_at_line(source, 3, 'reverse')
        self.assertEqual(owner_at_line(source, 5, 'next')['receiver'], 'IntermediateVectorTile')

    def test_anonymous_receiver_is_not_enclosing_class(self):
        # RDPro RasterFileRDD.accept (line162) belongs to an anonymous PathFilter.
        source = 'class RasterFileRDD {\n def paths = {\n new PathFilter {\n override def accept(path: Path): Boolean = true\n }\n }\n}'
        with self.assertRaises(ValueError):
            owner_at_line(source, 4, 'accept')

    def test_bodyless_declaration_does_not_claim_following_initializer(self):
        source = 'object A {\n case class Empty(x: Int)\n List(1).foreach { x =>\n def local = x\n }\n def member = 1\n}'
        with self.assertRaises(ValueError):
            owner_at_line(source, 4, 'local')
        self.assertEqual(owner_at_line(source, 6, 'member')['receiver'], 'A')

    def test_local_named_class_members_are_not_qualified_public_members(self):
        source = 'class A {\n def f = {\n class Local {\n def g = 1\n }\n }\n}'
        with self.assertRaises(ValueError):
            owner_at_line(source, 4, 'g')

    def test_multiline_owner_header_remains_supported(self):
        source = 'class A\n private (x: Int)\n extends Base\n with Serializable\n{\n def f = x\n}'
        self.assertEqual(owner_at_line(source, 6, 'f')['owner_kind'], 'class')

    def test_wrong_or_missing_site(self):
        for source, line, name in [('def f = 1', 1, 'f'), ('object A { def f = 1 }', 1, 'g'), ('object A {\n def f = 1', 2, 'f')]:
            with self.subTest(source=source), self.assertRaises(ValueError):
                owner_at_line(source, line, name)


if __name__ == '__main__':
    unittest.main()
