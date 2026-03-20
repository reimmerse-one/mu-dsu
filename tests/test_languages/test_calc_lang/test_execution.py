"""Basic CalcLang execution tests."""

from mu_dsu.languages.calc_lang import create_interpreter


class TestCalcLangBasics:
    def test_var_and_assign(self):
        interp = create_interpreter()
        interp.run('var x = 10; x = x + 5;')
        assert interp.env.get("x") == 15

    def test_arithmetic(self):
        interp = create_interpreter()
        interp.run('var x = (2 + 3) * 4;')
        assert interp.env.get("x") == 20

    def test_comparison(self):
        interp = create_interpreter()
        interp.run('var x = 5 > 3;')
        assert interp.env.get("x") is True

    def test_simple_for_loop(self):
        interp = create_interpreter()
        interp.run('var sum = 0; for (var i = 0; i < 5; i = i + 1) { sum = sum + i; };')
        assert interp.env.get("sum") == 10  # 0+1+2+3+4

    def test_for_with_increment(self):
        interp = create_interpreter()
        interp.run('var count = 0; for (var i = 0; i < 3; ++i) { count = count + 1; };')
        assert interp.env.get("count") == 3

    def test_while_loop(self):
        interp = create_interpreter()
        interp.run('var n = 10; while (n > 0) { n = n - 3; };')
        assert interp.env.get("n") <= 0

    def test_nested_for(self):
        interp = create_interpreter()
        interp.run("""\
var total = 0;
for (var i = 0; i < 3; ++i) {
    for (var j = 0; j < 4; ++j) {
        total = total + 1;
    };
};
""")
        assert interp.env.get("total") == 12  # 3 * 4

    def test_execution_modes_recorded(self):
        interp = create_interpreter()
        interp.env.set("__exec_modes__", [])
        interp.run('for (var i = 0; i < 2; ++i) { var x = i; };')
        assert interp.env.get("__exec_modes__") == ["sequential"]

    def test_float_literals(self):
        interp = create_interpreter()
        interp.run('var x = 2.5;')
        assert interp.env.get("x") == 2.5
