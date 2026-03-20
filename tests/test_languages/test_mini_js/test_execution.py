"""Basic MiniJS language execution tests."""

from mu_dsu.languages.mini_js import create_interpreter


class TestMiniJSBasics:
    def test_var_declaration(self):
        interp = create_interpreter()
        interp.run('var x = 42;')
        assert interp.env.get("x") == 42

    def test_string_literal(self):
        interp = create_interpreter()
        interp.run('var s = "hello";')
        assert interp.env.get("s") == "hello"

    def test_set_font_size(self):
        interp = create_interpreter()
        interp.run('set font size 24;')
        assert interp.env.get("__font_size__") == 24

    def test_set_font_color(self):
        interp = create_interpreter()
        interp.run('set font color "red";')
        assert interp.env.get("__font_color__") == "red"

    def test_print_outputs(self):
        interp = create_interpreter()
        interp.run('set font size 14; set font color "blue"; print "test";')
        output = interp.env.get("__output__")
        assert len(output) == 1
        assert output[0]["text"] == "test"
        assert output[0]["size"] == 14
        assert output[0]["color"] == "blue"

    def test_member_access(self):
        interp = create_interpreter()
        interp.env.set("obj", {"name": "Alice", "age": 30})
        interp.run('var n = obj.name;')
        assert interp.env.get("n") == "Alice"

    def test_arithmetic(self):
        interp = create_interpreter()
        interp.run('var x = 2 + 3 * 4;')
        assert interp.env.get("x") == 14
