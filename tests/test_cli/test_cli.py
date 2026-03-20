"""CLI integration tests."""

from click.testing import CliRunner

from mu_dsu.cli.main import cli


@staticmethod
def _write_program(tmp_path, filename, content):
    f = tmp_path / filename
    f.write_text(content)
    return str(f)


class TestLangCommands:
    def test_lang_list(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["lang", "list"])
        assert result.exit_code == 0
        assert "hooverlang" in result.output
        assert "minijs" in result.output
        assert "calclang" in result.output

    def test_lang_info(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["lang", "info", "hooverlang"])
        assert result.exit_code == 0
        assert "sm.state" in result.output
        assert "sm.program" in result.output
        assert "Slices" in result.output

    def test_lang_info_unknown(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["lang", "info", "nonexistent"])
        assert result.exit_code != 0


class TestRunCommand:
    def test_run_hooverlang(self, tmp_path):
        program = tmp_path / "test.sm"
        program.write_text("""\
states
  on  = turn-on
  off = turn-off
events
  click = get.click()
transitions
  on  { click => off }
  off { click => on  }
""")
        runner = CliRunner()
        result = runner.invoke(cli, ["run", str(program), "--lang", "hooverlang"])
        assert result.exit_code == 0

    def test_run_minijs(self, tmp_path):
        program = tmp_path / "test.mjs"
        program.write_text('var x = 42; print "hello";')
        runner = CliRunner()
        result = runner.invoke(cli, ["run", str(program), "--lang", "minijs"])
        assert result.exit_code == 0

    def test_run_calclang(self, tmp_path):
        program = tmp_path / "test.calc"
        program.write_text("var x = 2 + 3;")
        runner = CliRunner()
        result = runner.invoke(cli, ["run", str(program), "--lang", "calclang"])
        assert result.exit_code == 0

    def test_run_auto_detect_extension(self, tmp_path):
        program = tmp_path / "test.sm"
        program.write_text("""\
states
  idle = init
events
  go = get.go()
transitions
  idle { go => idle }
""")
        runner = CliRunner()
        result = runner.invoke(cli, ["run", str(program)])
        assert result.exit_code == 0

    def test_run_no_lang_no_ext(self, tmp_path):
        program = tmp_path / "test.txt"
        program.write_text("hello")
        runner = CliRunner()
        result = runner.invoke(cli, ["run", str(program)])
        assert result.exit_code != 0


class TestParseCommand:
    def test_parse_hooverlang(self, tmp_path):
        program = tmp_path / "test.sm"
        program.write_text("""\
states
  on  = turn-on
  off = turn-off
events
  click = get.click()
transitions
  on  { click => off }
  off { click => on  }
""")
        runner = CliRunner()
        result = runner.invoke(cli, ["parse", str(program), "--lang", "hooverlang"])
        assert result.exit_code == 0
        assert "start" in result.output
        assert "states_section" in result.output
        assert "trans_rule" in result.output


class TestAnalyzeCommand:
    def test_analyze_ast(self, tmp_path):
        program = tmp_path / "test.sm"
        program.write_text("""\
states
  on  = turn-on
  off = turn-off
events
  click = get.click()
transitions
  on  { click => off }
  off { click => on  }
""")
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", str(program), "--lang", "hooverlang"])
        assert result.exit_code == 0
        assert "Features" in result.output
        assert "Micro-languages" in result.output


class TestVersion:
    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output
