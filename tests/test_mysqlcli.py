#!/usr/bin/env python3
"""mysql-cli CLI 冒烟测试 —— stdlib `unittest`，零第三方依赖。

CLI 本体是没有 `.py` 后缀的单文件（`mysql-cli/cli/mysql-cli`），用 `SourceFileLoader` 载入。
覆盖：Flyway checksum 算法（注释/空白/行分隔语义）＋ 迁移扫描；导入的 DDL 推断；
参数解析与全局旗标；连接取值环（命令行 → env → toml → 默认）；写闸；migrate-check 目录映射；
`import` 的预演路径（不连库即可断言生成的 DDL）。**不连真库**。

运行：`python3 -m unittest discover -s tests -v`（需 Python 3.11+，`tomllib`）
"""
from __future__ import annotations

import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
import re
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest import mock

CLI = Path(__file__).resolve().parents[1] / "mysql-cli" / "cli" / "mysql-cli"


def _load_cli():
    loader = importlib.machinery.SourceFileLoader("mysql_cli_mod", str(CLI))
    spec = importlib.util.spec_from_loader("mysql_cli_mod", loader)
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


mc = _load_cli()


def _ctx(root, cfg=None, env_files=None, conn_opts=None, json_mode=False, dry_run=False):
    return mc.Context(Path(root), cfg or {}, env_files or [], conn_opts or {}, json_mode, dry_run)


class TestFlywayChecksum(unittest.TestCase):
    def test_matches_algorithm_definition(self):
        """与 Flyway 12 定义逐行走一遍 CRC32 的结果一致（独立复算，防手误改动）。"""
        text = "A\nB\r\nC\n"

        def manual(s):
            crc = 0
            for line in re.split(r"\r\n|\r|\n", s):
                crc = zlib.crc32(line.rstrip().encode("utf-8"), crc)
            return crc - 2**32 if crc >= 2**31 else crc

        self.assertEqual(mc.flyway_checksum(text), manual(text))

    def test_stable_anchor(self):
        """固定锚点：`SELECT 1;\\n` 的实算值（改算法会立刻变红）。"""
        self.assertEqual(mc.flyway_checksum("SELECT 1;\n"), 78787420)
        self.assertEqual(mc.flyway_checksum("A\nB\n"), 812207111)

    def test_comment_change_alters_checksum(self):
        """注释计入 checksum：改注释与改 DDL 等价（已执行迁移定版冻结）。"""
        base = "-- 注释\nSELECT 1;\n"
        edited = "-- 注释改了\nSELECT 1;\n"
        self.assertNotEqual(mc.flyway_checksum(base), mc.flyway_checksum(edited))

    def test_trailing_whitespace_ignored_leading_kept(self):
        """算法是 `rstrip()`（非 `trim()`）：行尾空白不算，行首空白算。"""
        self.assertEqual(mc.flyway_checksum("SELECT 1;   \n"), mc.flyway_checksum("SELECT 1;\n"))
        self.assertNotEqual(mc.flyway_checksum("  SELECT 1;\n"), mc.flyway_checksum("SELECT 1;\n"))

    def test_line_separators_follow_java_readline(self):
        """行分隔按 Java `readLine()`（`\\r\\n`／`\\n`／`\\r` 同义）。"""
        lf = mc.flyway_checksum("A\nB\n")
        self.assertEqual(lf, mc.flyway_checksum("A\r\nB\r\n"))
        self.assertEqual(lf, mc.flyway_checksum("A\rB\r"))

    def test_read_migrations_sorted_and_filtered(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "V2__b.sql").write_text("SELECT 2;", encoding="utf-8")
            (d / "V10__c.sql").write_text("SELECT 10;", encoding="utf-8")
            (d / "notes.sql").write_text("x", encoding="utf-8")
            found = mc.read_migrations(d)
            self.assertEqual(list(found), [2, 10])
            self.assertEqual(found[2][0], "V2__b.sql")
            self.assertEqual(found[10][1], mc.flyway_checksum("SELECT 10;"))


class TestDdlInfer(unittest.TestCase):
    def test_split_values_respects_quotes(self):
        self.assertEqual(mc._split_values("1,'a,b',3"), ["1", "'a,b'", "3"])
        self.assertEqual(mc._split_values("'it\\'s',2"), ["'it\\'s'", "2"])

    def test_infer_types(self):
        self.assertEqual(mc._infer("created_at", ["2024-01-01 10:00:00"]), "DATETIME")
        self.assertEqual(mc._infer("biz_date", ["2024-01-01"]), "DATE")
        self.assertEqual(mc._infer("amount", ["1.25"]), "DECIMAL(20,4)")
        self.assertEqual(mc._infer("qty", ["12"]), "BIGINT")
        self.assertEqual(mc._infer("user_id", ["7"]), "VARCHAR(255)")   # ID 后缀优先
        self.assertEqual(mc._infer("remark", ["hi"]), "TEXT")
        self.assertEqual(mc._infer("anything", []), "TEXT")

    def test_build_ddl_insert_inference(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "a.sql").write_text(
                "INSERT INTO `t_user`(`id`,`name`,`created_at`) "
                "VALUES (1,'alice','2024-01-01 10:00:00'),(2,'bob','2024-01-02 11:00:00');\n",
                encoding="utf-8")
            ddl = mc.build_ddl(sorted(d.glob("*.sql")), "app", drop=False)
            self.assertIn("USE `app`;", ddl)
            self.assertIn("CREATE TABLE IF NOT EXISTS `t_user`", ddl)
            self.assertIn("`created_at` DATETIME", ddl)
            ddl2 = mc.build_ddl(sorted(d.glob("*.sql")), "app", drop=True)
            self.assertIn("DROP TABLE IF EXISTS `t_user`;", ddl2)


class TestParse(unittest.TestCase):
    def test_parse_pos_and_opts(self):
        pos, opts = mc._parse(["deck", "--db", "app", "--json", "--k=v"])
        self.assertEqual(pos, ["deck"])
        self.assertEqual(opts["db"], "app")
        self.assertTrue(opts["json"])
        self.assertEqual(opts["k"], "v")

    def test_parse_bool_flag(self):
        _pos, opts = mc._parse(["--apply"], ("apply",))
        self.assertTrue(opts["apply"])

    def test_split_globals(self):
        root, envs, js, dry, co, rest = mc._split_globals(
            ["--root", "/p", "--env-file", "a.env", "--env-file=b.env",
             "--host", "h", "--port=3307", "--db", "app", "--json", "query", "SELECT 1"])
        self.assertEqual(root, "/p")
        self.assertEqual(envs, ["a.env", "b.env"])
        self.assertTrue(js)
        self.assertFalse(dry)
        self.assertEqual(co, {"host": "h", "port": "3307", "db": "app"})
        self.assertEqual(rest, ["query", "SELECT 1"])


class TestConnection(unittest.TestCase):
    def test_defaults(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            conn = _ctx(".").connection()
        self.assertEqual(conn, mc.Conn("127.0.0.1", "3306", "root", ""))

    def test_toml_then_cli(self):
        cfg = {"connection": {"host": "db.internal", "port": 3307}}
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(_ctx(".", cfg=cfg).connection().host, "db.internal")
            # 命令行覆盖 toml
            c = _ctx(".", cfg=cfg, conn_opts={"host": "cli.host"}).connection()
        self.assertEqual(c.host, "cli.host")
        self.assertEqual(c.port, "3307")

    def test_env_file_beats_toml(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "infra.env").write_text("MYSQL_HOST=env.host\nMYSQL_PASSWORD=pw\n", encoding="utf-8")
            cfg = {"connection": {"env_file": "infra.env", "host": "toml.host"}}
            with mock.patch.dict(os.environ, {}, clear=True):
                conn = _ctx(tmp, cfg=cfg).connection()
        self.assertEqual(conn.host, "env.host")
        self.assertEqual(conn.password, "pw")

    def test_var_name_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "x.env").write_text("MT_DB_HOST=custom.host\n", encoding="utf-8")
            cfg = {"connection": {"env_file": "x.env", "host_var": "MT_DB_HOST"}}
            with mock.patch.dict(os.environ, {}, clear=True):
                conn = _ctx(tmp, cfg=cfg).connection()
        self.assertEqual(conn.host, "custom.host")

    def test_process_env_beats_toml(self):
        cfg = {"connection": {"host": "toml.host"}}
        with mock.patch.dict(os.environ, {"MYSQL_HOST": "proc.host"}, clear=True):
            conn = _ctx(".", cfg=cfg).connection()
        self.assertEqual(conn.host, "proc.host")


class TestWriteGate(unittest.TestCase):
    def test_unconfigured_allows(self):
        self.assertIsNone(mc._write_gate(_ctx(".", cfg={}), "any.host"))

    def test_blocks_non_whitelist(self):
        cfg = {"write_gate": {"allow_hosts": ["127.0.0.1"]}}
        self.assertIsNone(mc._write_gate(_ctx(".", cfg=cfg), "127.0.0.1"))
        self.assertIsNotNone(mc._write_gate(_ctx(".", cfg=cfg), "prod.db"))


class TestMigrationDirs(unittest.TestCase):
    def test_dir_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            dirs = mc._migration_dirs(_ctx(tmp), {"dir": "db/migration"})
        self.assertEqual(list(dirs), [""])
        self.assertTrue(str(dirs[""]).endswith("db/migration"))

    def test_toml_map(self):
        cfg = {"migrations": {"app": "db/m/app", "org": "/abs/org"}}
        dirs = mc._migration_dirs(_ctx("/root", cfg=cfg), {})
        self.assertEqual(set(dirs), {"app", "org"})
        self.assertTrue(str(dirs["app"]).endswith("db/m/app"))
        self.assertEqual(str(dirs["org"]), "/abs/org")


class TestImportDryRun(unittest.TestCase):
    def test_preview_prints_ddl_without_db(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "seed.sql").write_text(
                "INSERT INTO `t_kv`(`k`,`v`) VALUES ('a','1'),('b','2');\n", encoding="utf-8")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = mc.cmd_import([tmp, "app"], _ctx(tmp))
            out = buf.getvalue()
        self.assertEqual(rc, 0)
        self.assertIn("仅预演", out)
        self.assertIn("CREATE TABLE IF NOT EXISTS `t_kv`", out)

    def test_rejects_bad_dir(self):
        with self.assertRaises(mc.MySQLError):
            mc.cmd_import(["/no/such/dir", "app"], _ctx("."))

    def test_rejects_bad_db_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "a.sql").write_text("SELECT 1;", encoding="utf-8")
            with self.assertRaises(mc.MySQLError):
                mc.cmd_import([tmp, "bad-name"], _ctx(tmp))


class TestDispatchAndOutput(unittest.TestCase):
    def test_unknown_command_exit_2(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            rc = mc.dispatch(["nope"], _ctx("."))
        self.assertEqual(rc, 2)
        self.assertIn("未知命令", err.getvalue())

    def test_help_exit_0(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = mc.main(["--help"])
        self.assertEqual(rc, 0)
        self.assertIn("mysql-cli ping", buf.getvalue())

    def test_rows_to_table(self):
        header, body = mc.rows_to_table("a\tb\n1\t2\n3\t4\n")
        self.assertEqual(header, ["a", "b"])
        self.assertEqual(body, [["1", "2"], ["3", "4"]])
        self.assertEqual(mc.rows_to_table(""), ([], []))

    def test_render_table_empty(self):
        self.assertEqual(mc.render_table(["h"], []), "（无）")

    def test_render_table_cjk_align(self):
        table = mc.render_table(["表名", "值"], [["中", "1"], ["abcd", "2"]])
        lines = table.splitlines()
        self.assertEqual(len(lines), 4)          # 表头 + 分隔 + 2 行


class TestPasswordInjection(unittest.TestCase):
    def test_mysql_pwd_never_on_argv(self):
        """口令只进 env（MYSQL_PWD），绝不出现在命令行 argv。"""
        with mock.patch("subprocess.run") as run:
            run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            mc.run_sql(mc.Conn("h", "3306", "u", "sekret"), "SELECT 1")
        cmd = run.call_args[0][0]
        env = run.call_args[1]["env"]
        self.assertEqual(env["MYSQL_PWD"], "sekret")
        self.assertNotIn("sekret", cmd)


class TestJsonOutput(unittest.TestCase):
    def test_query_json_shape(self):
        with mock.patch("subprocess.run") as run:
            run.return_value = mock.Mock(returncode=0, stdout="id\tname\n1\talice\n", stderr="")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = mc.cmd_query(["SELECT * FROM t"], _ctx(".", json_mode=True))
        self.assertEqual(rc, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["columns"], ["id", "name"])
        self.assertEqual(data["rows"], [["1", "alice"]])


if __name__ == "__main__":
    unittest.main()
