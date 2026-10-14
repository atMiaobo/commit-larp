import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "gitlarp"


class ModesTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="/dev/null",
                        GIT_AUTHOR_NAME="Test", GIT_AUTHOR_EMAIL="test@example.invalid",
                        GIT_COMMITTER_NAME="Test", GIT_COMMITTER_EMAIL="test@example.invalid")
        for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
            self.env.pop(name, None)
        self.git("init", "-q")

    def command(self, *args, check=True):
        return subprocess.run(args, cwd=self.root, env=self.env, check=check,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def git(self, *args):
        return self.command("git", *args).stdout

    def larp(self, *args, check=True):
        return self.command("bash", str(SCRIPT), *args, check=check)

    def write(self, name, data):
        (self.root / name).write_bytes(data)

    def count(self):
        return int(self.git("rev-list", "--count", "HEAD"))

    def assert_clean(self):
        self.assertEqual(self.git("status", "--porcelain"), b"")

    def test_mode_setting(self):
        self.assertEqual(self.larp("mode").stdout, b"file\n")
        self.larp("mode", "word")
        self.assertEqual(self.git("config", "--local", "gitlarp.mode"), b"word\n")
        self.assertNotEqual(self.larp("mode", "invalid", check=False).returncode, 0)
        self.assertEqual(self.larp("mode").stdout, b"word\n")

    def test_lines_add_replace_delete(self):
        self.larp("mode", "line")
        self.write("file", b"one\ntwo\nthree")
        self.larp("commit")
        self.assertEqual(self.count(), 3)
        self.assertEqual(self.git("show", "HEAD~1:file"), b"one\ntwo\n")
        self.write("file", b"ONE\ntwo\nTHREE")
        self.larp("commit")
        self.assertEqual(self.count(), 5)
        self.assertEqual(self.git("show", "HEAD~1:file"), b"ONE\ntwo\nthree")
        (self.root / "file").unlink()
        self.larp("commit")
        self.assertEqual(self.count(), 8)
        self.assertEqual(self.git("ls-tree", "--name-only", "HEAD"), b"")
        self.assert_clean()

    def test_words_and_whitespace(self):
        self.larp("mode", "word")
        original = "one  two\t三\nfour".encode()
        self.write("file", original)
        self.larp("commit")
        self.assertEqual(self.count(), 4)
        self.assertEqual(self.git("show", "HEAD~1:file"), "one  two\t三".encode())
        target = "one\ttwo\t三\nFOUR \n".encode()
        self.write("file", target)
        self.larp("commit")
        self.assertEqual(self.count(), 7)
        self.assertEqual(self.git("show", "HEAD:file"), target)
        self.assertEqual((self.root / "file").read_bytes(), target)
        self.assert_clean()

    def test_special_files_and_names(self):
        self.larp("mode", "word")
        files = {"binary": b"a\0b", "invalid": b"\xff", "empty": b"",
                 ":wild*\nname": b"hello world", "crlf": b"a\r\nb\r\n"}
        for name, content in files.items():
            self.write(name, content)
        (self.root / "link").symlink_to("empty")
        self.larp("commit")
        for name, content in files.items():
            self.assertEqual(self.git("show", f"HEAD:{name}"), content)
        self.assertEqual(self.git("show", "HEAD:link"), b"empty")
        self.assert_clean()
        (self.root / "empty").chmod(0o755)
        before = self.count()
        self.larp("commit")
        self.assertEqual(self.count(), before + 1)
        self.assertTrue(self.git("ls-tree", "HEAD", "empty").startswith(b"100755"))

    def test_unequal_edits_and_whitespace_only(self):
        self.larp("mode", "line")
        self.write("file", b"a\nb\nc\nd\ne\nf\n")
        self.larp("commit")
        self.write("file", b"x\ny\nb\nc\nz\nf\nextra")
        self.larp("commit")
        self.assertEqual(self.git("show", "HEAD:file"), b"x\ny\nb\nc\nz\nf\nextra")
        self.assert_clean()
        self.larp("mode", "word")
        self.write("file", b" \t\n")
        self.larp("commit")
        self.assertEqual(self.git("show", "HEAD:file"), b" \t\n")
        self.write("file", b"")
        self.larp("commit")
        self.assertEqual(self.git("show", "HEAD:file"), b"")
        self.assert_clean()
        before = self.count()
        self.larp("commit")
        self.assertEqual(self.count(), before)

    def test_staged_and_unstaged_are_isolated(self):
        self.write("alpha", b"old\n")
        self.write("beta", b"old\n")
        self.larp("commit")
        self.write("alpha", b"staged\n")
        self.write("beta", b"beta\n")
        self.git("add", ".")
        self.write("alpha", b"unstaged\nextra\n")
        self.larp("mode", "line")
        self.larp("commit")
        self.assertEqual(self.count(), 5)
        self.assertEqual(self.git("show", "HEAD:alpha"), b"unstaged\nextra\n")
        self.assertEqual(self.git("show", "HEAD~1:beta"), b"old\n")
        self.assert_clean()

    def test_hook_failure_preserves_work_and_can_resume(self):
        self.larp("mode", "line")
        self.write("file", b"one\ntwo\nthree\n")
        hook = self.root / ".git/hooks/pre-commit"
        hook.write_text("#!/usr/bin/env bash\n! git rev-parse --verify HEAD >/dev/null 2>&1\n")
        hook.chmod(0o755)
        self.assertNotEqual(self.larp("commit", check=False).returncode, 0)
        self.assertEqual(self.count(), 1)
        self.assertEqual((self.root / "file").read_bytes(), b"one\ntwo\nthree\n")
        hook.unlink()
        self.larp("commit")
        self.assertEqual(self.count(), 3)
        self.assert_clean()

    def assert_undo_mode(self, mode):
        self.write("base", b"original\n")
        self.larp("commit")
        base = self.git("rev-parse", "HEAD")
        self.larp("mode", mode)
        self.write("base", b"updated text\nextra line\n")
        self.write("new", b"new text\n")
        self.larp("commit")
        self.assertGreater(self.count(), 1)
        self.write("new", b"later staged edit\n")
        self.git("add", "new")
        self.write("new", b"later unstaged edit\n")
        self.write("untracked", b"keep me\n")
        staged = self.git("write-tree")
        self.larp("undo")
        self.assertEqual(self.git("rev-parse", "HEAD"), base)
        self.assertEqual(self.git("write-tree"), staged)
        self.assertEqual((self.root / "base").read_bytes(), b"updated text\nextra line\n")
        self.assertEqual((self.root / "new").read_bytes(), b"later unstaged edit\n")
        self.assertEqual((self.root / "untracked").read_bytes(), b"keep me\n")
        self.assertNotEqual(self.larp("undo", check=False).returncode, 0)
        self.larp("commit")
        self.assert_clean()

    def test_undo_file(self):
        self.assert_undo_mode("file")

    def test_undo_line(self):
        self.assert_undo_mode("line")

    def test_undo_word(self):
        self.assert_undo_mode("word")

    def test_undo_first_run(self):
        for mode in ("file", "line", "word"):
            with self.subTest(mode=mode):
                self.larp("mode", mode)
                self.write("file", b"one two\nthree four\n")
                self.larp("commit")
                staged = self.git("write-tree")
                branch = self.git("symbolic-ref", "HEAD")
                self.larp("undo")
                self.assertNotEqual(self.command("git", "rev-parse", "--verify", "HEAD", check=False).returncode, 0)
                self.assertEqual(self.git("symbolic-ref", "HEAD"), branch)
                self.assertEqual(self.git("write-tree"), staged)
                self.assertEqual((self.root / "file").read_bytes(), b"one two\nthree four\n")

    def test_undo_refuses_changed_head_and_branch(self):
        self.assertNotEqual(self.larp("undo", check=False).returncode, 0)
        self.write("file", b"one\n")
        self.larp("commit")
        original_branch = self.git("symbolic-ref", "--short", "HEAD").decode().strip()
        self.git("switch", "-c", "other")
        self.assertNotEqual(self.larp("undo", check=False).returncode, 0)
        self.git("switch", original_branch)

if __name__ == "__main__":
    unittest.main()
