"""
Advanced arithmetic tests.
Tests arithmetic operations and comparisons.
"""

import pytest
from vibeprolog import PrologInterpreter


class TestBasicArithmetic:
    """Basic arithmetic operations"""

    def test_addition(self):
        prolog = PrologInterpreter()

        result = prolog.query_once("X is 2 + 3")
        assert result is not None
        assert result['X'] == 5

        result = prolog.query_once("X is 10 + 20")
        assert result is not None
        assert result['X'] == 30

    def test_subtraction(self):
        prolog = PrologInterpreter()

        result = prolog.query_once("X is 10 - 3")
        assert result is not None
        assert result['X'] == 7

        result = prolog.query_once("X is 5 - 8")
        assert result is not None
        assert result['X'] == -3

    def test_multiplication(self):
        prolog = PrologInterpreter()

        result = prolog.query_once("X is 4 * 5")
        assert result is not None
        assert result['X'] == 20

        result = prolog.query_once("X is 7 * 8")
        assert result is not None
        assert result['X'] == 56

    def test_division(self):
        prolog = PrologInterpreter()

        result = prolog.query_once("X is 10 / 2")
        assert result is not None
        assert result['X'] == 5.0

        result = prolog.query_once("X is 7 / 2")
        assert result is not None
        assert result['X'] == 3.5

    def test_integer_division(self):
        prolog = PrologInterpreter()

        result = prolog.query_once("X is 10 // 3")
        assert result is not None
        assert result['X'] == 3

        result = prolog.query_once("X is 20 // 6")
        assert result is not None
        assert result['X'] == 3

    def test_modulo(self):
        prolog = PrologInterpreter()

        result = prolog.query_once("X is 10 mod 3")
        assert result is not None
        assert result['X'] == 1

        result = prolog.query_once("X is 17 mod 5")
        assert result is not None
        assert result['X'] == 2

    @pytest.mark.larl_exclude
    def test_remainder(self):
        prolog = PrologInterpreter()

        result = prolog.query_once("X is 10 rem 3")
        assert result is not None
        assert result['X'] == 1

        result = prolog.query_once("X is 17 rem 5")
        assert result is not None
        assert result['X'] == 2

        # Test negative operands
        result = prolog.query_once("X is (-10) rem 3")
        assert result is not None
        assert result['X'] == -1

        result = prolog.query_once("X is 10 rem (-3)")
        assert result is not None
        assert result['X'] == 1

        result = prolog.query_once("X is (-10) rem (-3)")
        assert result is not None
        assert result['X'] == -1

    @pytest.mark.parametrize("expr, expected", [
        ("X is 7 div 2", 3),
        ("X is 20 div 6", 3),
        ("X is -7 div 2", -4),
    ])
    def test_div_operator(self, expr, expected):
        prolog = PrologInterpreter()
        result = prolog.query_once(expr)
        assert result is not None
        assert result['X'] == expected

    @pytest.mark.parametrize("expr, expected", [
        ("X is 7 rem 2", 1),
        ("X is 20 rem 6", 2),
        ("X is -7 rem 2", -1),
        ("X is 7 rem -2", 1),
        ("X is -7 rem -2", -1),
    ])
    def test_rem_operator(self, expr, expected):
        prolog = PrologInterpreter()
        result = prolog.query_once(expr)
        assert result is not None
        assert result['X'] == expected

    @pytest.mark.parametrize("expr1, expr2", [
        ("X is 7 div 2", "Y is 7 // 2"),
        ("X is -7 div 2", "Y is -7 // 2"),
    ])
    def test_div_matches_floor_division(self, expr1, expr2):
        prolog = PrologInterpreter()
        result1 = prolog.query_once(expr1)
        result2 = prolog.query_once(expr2)
        assert result1 is not None
        assert result2 is not None
        assert result1['X'] == result2['Y']

    def test_rem_current_op(self):
        prolog = PrologInterpreter()
        # Verify rem is defined with correct precedence and associativity
        assert prolog.has_solution("current_op(400, yfx, rem)")


class TestArithmeticPrecedence:
    """Operator precedence in arithmetic"""

    def test_multiplication_before_addition(self):
        prolog = PrologInterpreter()

        result = prolog.query_once("X is 2 + 3 * 4")
        assert result is not None
        assert result['X'] == 14  # Not 20

    def test_division_before_subtraction(self):
        prolog = PrologInterpreter()

        result = prolog.query_once("X is 10 - 6 / 2")
        assert result is not None
        assert result['X'] == 7.0  # Not 2.0

    def test_left_to_right(self):
        prolog = PrologInterpreter()

        result = prolog.query_once("X is 10 - 3 - 2")
        assert result is not None
        assert result['X'] == 5  # (10 - 3) - 2, not 10 - (3 - 2)

    @pytest.mark.parametrize("query, expected", [
        ("X is 10 + 7 div 2", 13),
        ("X is 7 div 2 * 3", 9),
    ])
    def test_div_precedence(self, query, expected):
        prolog = PrologInterpreter()
        result = prolog.query_once(query)
        assert result is not None
        assert result['X'] == expected

    @pytest.mark.parametrize("query, expected", [
        ("X is 10 + 7 rem 2", 11),
        ("X is 7 rem 2 * 3", 3),
        ("X is 17 rem 5 rem 2", 0),  # (17 rem 5) rem 2 = 2 rem 2 = 0
    ])
    def test_rem_precedence(self, query, expected):
        prolog = PrologInterpreter()
        result = prolog.query_once(query)
        assert result is not None
        assert result['X'] == expected


class TestComplexExpressions:
    """Complex arithmetic expressions"""

    def test_nested_operations(self):
        prolog = PrologInterpreter()

        result = prolog.query_once("X is (2 + 3) * (4 + 1)")
        assert result is not None
        assert result['X'] == 25

        result = prolog.query_once("X is 2 * (3 + 4) - 1")
        assert result is not None
        assert result['X'] == 13

    def test_mixed_types(self):
        prolog = PrologInterpreter()

        result = prolog.query_once("X is 5 + 2.5")
        assert result is not None
        assert result['X'] == 7.5

        result = prolog.query_once("X is 10 / 4")
        assert result is not None
        assert isinstance(result['X'], float)

    def test_negative_numbers(self):
        prolog = PrologInterpreter()

        result = prolog.query_once("X is -5 + 3")
        assert result is not None
        assert result['X'] == -2

        result = prolog.query_once("X is 10 - -5")
        assert result is not None
        assert result['X'] == 15

    @pytest.mark.larl_exclude
    def test_unary_minus_with_spaces(self):
        """Test unary minus operator with spaces."""
        prolog = PrologInterpreter()

        result = prolog.query_once("X is - 8")
        assert result is not None
        assert result['X'] == -8

        result = prolog.query_once("X is - 8.5")
        assert result is not None
        assert result['X'] == -8.5

        result = prolog.query_once("X is 14 + ( - 8 ) + 1")
        assert result is not None
        assert result['X'] == 7

        result = prolog.query_once("X is 5 + (- 3)")
        assert result is not None
        assert result['X'] == 2


class TestArithmeticComparisons:
    """Arithmetic comparison operators"""

    def test_equal(self):
        prolog = PrologInterpreter()

        assert prolog.has_solution("5 =:= 5")
        assert prolog.has_solution("2 + 3 =:= 5")
        assert not prolog.has_solution("5 =:= 6")

    def test_less_than(self):
        prolog = PrologInterpreter()

        assert prolog.has_solution("3 < 5")
        assert prolog.has_solution("2 + 1 < 5")
        assert not prolog.has_solution("5 < 3")
        assert not prolog.has_solution("5 < 5")

    def test_greater_than(self):
        prolog = PrologInterpreter()

        assert prolog.has_solution("5 > 3")
        assert prolog.has_solution("10 - 2 > 5")
        assert not prolog.has_solution("3 > 5")
        assert not prolog.has_solution("5 > 5")

    def test_less_equal(self):
        prolog = PrologInterpreter()

        assert prolog.has_solution("3 =< 5")
        assert prolog.has_solution("5 =< 5")
        assert not prolog.has_solution("6 =< 5")

    def test_greater_equal(self):
        prolog = PrologInterpreter()

        assert prolog.has_solution("5 >= 3")
        assert prolog.has_solution("5 >= 5")
        assert not prolog.has_solution("3 >= 5")

    def test_not_equal(self):
        prolog = PrologInterpreter()

        # Basic integer inequality
        assert prolog.has_solution(r"5 =\= 3")
        assert prolog.has_solution(r"2 + 3 =\= 6")

        # Equality should fail
        assert not prolog.has_solution(r"5 =\= 5")
        assert not prolog.has_solution(r"10 - 5 =\= 5")

        # Float comparisons
        assert prolog.has_solution(r"5.0 =\= 3.0")
        assert not prolog.has_solution(r"5.0 =\= 5.0")

        # Negative numbers
        assert prolog.has_solution(r"-5 =\= 3")
        assert prolog.has_solution(r"5 =\= -3")
        assert not prolog.has_solution(r"-5 =\= -5")

        # Complex expressions
        assert prolog.has_solution(r"2 * 3 =\= 7")
        assert not prolog.has_solution(r"2 * 3 =\= 6")

        # Mixed int/float - same numeric value should be equal
        assert not prolog.has_solution(r"5 =\= 5.0")  # Same value, should fail
        assert prolog.has_solution(r"5 =\= 6.0")


class TestArithmeticInRules:
    """Using arithmetic in rules"""

    def test_arithmetic_condition(self):
        prolog = PrologInterpreter()
        prolog.consult_string("""
            adult(Person) :- age(Person, Age), Age >= 18.

            age(alice, 25).
            age(bob, 16).
            age(charlie, 18).
        """)

        assert prolog.has_solution("adult(alice)")
        assert not prolog.has_solution("adult(bob)")
        assert prolog.has_solution("adult(charlie)")

    def test_arithmetic_computation(self):
        prolog = PrologInterpreter()
        prolog.consult_string("""
            double(X, Y) :- Y is X * 2.
            square(X, Y) :- Y is X * X.
        """)

        result = prolog.query_once("double(5, Y)")
        assert result is not None
        assert result['Y'] == 10

        result = prolog.query_once("square(7, Y)")
        assert result is not None
        assert result['Y'] == 49

    def test_recursive_arithmetic(self):
        prolog = PrologInterpreter()
        prolog.consult_string("""
            sum_to(0, 0).
            sum_to(N, Sum) :- N > 0, N1 is N - 1, sum_to(N1, Sum1), Sum is Sum1 + N.
        """)

        result = prolog.query_once("sum_to(5, Sum)")
        assert result is not None
        assert result['Sum'] == 15  # 1+2+3+4+5

        result = prolog.query_once("sum_to(10, Sum)")
        assert result is not None
        assert result['Sum'] == 55  # 1+2+...+10


class TestArithmeticWithVariables:
    """Arithmetic with variables"""

    def test_variable_in_expression(self):
        prolog = PrologInterpreter()

        result = prolog.query_once("X = 5, Y is X + 3")
        assert result is not None
        assert result['X'] == 5
        assert result is not None
        assert result['Y'] == 8

    def test_multiple_variables(self):
        prolog = PrologInterpreter()

        result = prolog.query_once("X = 3, Y = 4, Z is X + Y")
        assert result is not None
        assert result['Z'] == 7

    def test_variable_reuse(self):
        prolog = PrologInterpreter()

        result = prolog.query_once("X = 5, Y is X * 2, Z is Y + X")
        assert result is not None
        assert result['X'] == 5
        assert result is not None
        assert result['Y'] == 10
        assert result is not None
        assert result['Z'] == 15


class TestArithmeticEdgeCases:
    """Edge cases in arithmetic"""

    def test_zero_operations(self):
        prolog = PrologInterpreter()

        result = prolog.query_once("X is 0 + 0")
        assert result is not None
        assert result['X'] == 0

        result = prolog.query_once("X is 5 * 0")
        assert result is not None
        assert result['X'] == 0

    def test_division_by_one(self):
        prolog = PrologInterpreter()

        result = prolog.query_once("X is 7 / 1")
        assert result is not None
        assert result['X'] == 7.0

    def test_modulo_edge_cases(self):
        prolog = PrologInterpreter()

        result = prolog.query_once("X is 5 mod 5")
        assert result is not None
        assert result['X'] == 0

        result = prolog.query_once("X is 3 mod 5")
        assert result is not None
        assert result['X'] == 3


class TestArithmeticInQueries:
    """Using arithmetic in complex queries"""

    def test_find_numbers_in_range(self):
        prolog = PrologInterpreter()
        prolog.consult_string("""
            num(1).
            num(2).
            num(3).
            num(4).
            num(5).
            num(6).
            num(7).
            num(8).
            num(9).
            num(10).

            in_range(X, Min, Max) :- num(X), X >= Min, X =< Max.
        """)

        results = list(prolog.query("in_range(X, 3, 7)"))
        values = {r['X'] for r in results}
        assert values == {3, 4, 5, 6, 7}

    def test_arithmetic_filtering(self):
        prolog = PrologInterpreter()
        prolog.consult_string("""
            value(1).
            value(2).
            value(3).
            value(4).
            value(5).

            even(X) :- value(X), 0 is X mod 2.
            odd(X) :- value(X), 1 is X mod 2.
        """)

        even_results = list(prolog.query("even(X)"))
        even_values = {r['X'] for r in even_results}
        assert even_values == {2, 4}

        odd_results = list(prolog.query("odd(X)"))
        odd_values = {r['X'] for r in odd_results}
        assert odd_values == {1, 3, 5}

    def test_pythagorean_triples(self):
        prolog = PrologInterpreter()
        prolog.consult_string("""
            num(3).
            num(4).
            num(5).
            num(6).
            num(7).
            num(8).
            num(9).
            num(10).

            pythagorean(A, B, C) :-
                num(A), num(B), num(C),
                A < B, B < C,
                C * C =:= A * A + B * B.
        """)

        results = list(prolog.query("pythagorean(A, B, C)"))
        assert len(results) >= 1

        # Check for 3-4-5 triple
        assert any(r['A'] == 3 and r['B'] == 4 and r['C'] == 5 for r in results)

        # Check for 6-8-10 triple
        assert any(r['A'] == 6 and r['B'] == 8 and r['C'] == 10 for r in results)


class TestArithmeticWithFindall:
    """Using findall with arithmetic"""

    def test_collect_computed_values(self):
        prolog = PrologInterpreter()
        prolog.consult_string("""
            num(1).
            num(2).
            num(3).
            num(4).
        """)

        # Collect squares
        result = prolog.query_once("findall(Y, (num(X), Y is X * X), Squares)")
        assert result is not None
        assert result['Squares'] == [1, 4, 9, 16]

    def test_collect_with_arithmetic_filter(self):
        prolog = PrologInterpreter()
        prolog.consult_string("""
            num(1).
            num(2).
            num(3).
            num(4).
            num(5).
        """)

        # Collect even numbers
        result = prolog.query_once("findall(X, (num(X), 0 is X mod 2), Evens)")
        assert result is not None
        assert set(result['Evens']) == {2, 4}


class TestISOArithmeticFunctions:
    """Tests for ISO-standard arithmetic functions"""

    @pytest.fixture
    def prolog(self):
        """Fixture to provide a fresh PrologInterpreter for each test."""
        return PrologInterpreter()

    @pytest.mark.parametrize("input_val,expected", [
        (5, 5),
        (3.14, 3.14),
        (-5, 5),
        (-3.14, 3.14),
        (0, 0),
    ])
    def test_abs(self, prolog, input_val, expected):
        """Test abs/1 with various inputs"""
        result = prolog.query_once(f"X is abs({input_val})")
        assert result is not None
        assert result['X'] == expected

    @pytest.mark.parametrize("left,right,expected", [
        (5, 3, 3),
        (10, 20, 10),
        (-5, 3, -5),
        (3.14, 2.71, 2.71),
    ])
    def test_min(self, prolog, left, right, expected):
        """Test min/2 with various inputs"""
        result = prolog.query_once(f"X is min({left}, {right})")
        assert result is not None
        assert result['X'] == expected

    @pytest.mark.parametrize("left,right,expected", [
        (5, 3, 5),
        (10, 20, 20),
        (-5, 3, 3),
        (3.14, 2.71, 3.14),
    ])
    def test_max(self, prolog, left, right, expected):
        """Test max/2 with various inputs"""
        result = prolog.query_once(f"X is max({left}, {right})")
        assert result is not None
        assert result['X'] == expected

    def test_sqrt_perfect_squares(self, prolog):
        """Test sqrt/1 with perfect squares"""
        result = prolog.query_once("X is sqrt(4)")
        assert result is not None
        assert result['X'] == 2.0

        result = prolog.query_once("X is sqrt(9)")
        assert result is not None
        assert result['X'] == 3.0

        result = prolog.query_once("X is sqrt(16)")
        assert result is not None
        assert result['X'] == 4.0

    def test_sqrt_non_perfect_squares(self, prolog):
        """Test sqrt/1 with non-perfect squares"""
        result = prolog.query_once("X is sqrt(2)")
        assert result is not None
        assert abs(result['X'] - 1.4142135623730951) < 1e-10

    def test_sqrt_zero(self, prolog):
        """Test sqrt/1 with zero"""
        result = prolog.query_once("X is sqrt(0)")
        assert result is not None
        assert result['X'] == 0.0

    def test_sin_basic(self, prolog):
        """Test sin/1 with basic values"""
        result = prolog.query_once("X is sin(0)")
        assert result is not None
        assert abs(result['X']) < 1e-10

        # sin(π/2) ≈ 1
        result = prolog.query_once("X is sin(1.5707963267948966)")
        assert result is not None
        assert abs(result['X'] - 1.0) < 1e-10

    def test_cos_basic(self, prolog):
        """Test cos/1 with basic values"""
        result = prolog.query_once("X is cos(0)")
        assert result is not None
        assert abs(result['X'] - 1.0) < 1e-10

        # cos(π) ≈ -1
        result = prolog.query_once("X is cos(3.141592653589793)")
        assert result is not None
        assert abs(result['X'] - (-1.0)) < 1e-10

    def test_tan_basic(self, prolog):
        """Test tan/1 with basic values"""
        result = prolog.query_once("X is tan(0)")
        assert result is not None
        assert abs(result['X']) < 1e-10

        # tan(π/4) ≈ 1
        result = prolog.query_once("X is tan(0.7853981633974483)")
        assert result is not None
        assert abs(result['X'] - 1.0) < 1e-10

    def test_exp_basic(self, prolog):
        """Test exp/1 with basic values"""
        result = prolog.query_once("X is exp(0)")
        assert result is not None
        assert abs(result['X'] - 1.0) < 1e-10

        result = prolog.query_once("X is exp(1)")
        assert result is not None
        assert abs(result['X'] - 2.718281828459045) < 1e-10

    def test_log_basic(self, prolog):
        """Test log/1 (natural logarithm) with basic values"""
        result = prolog.query_once("X is log(1)")
        assert result is not None
        assert abs(result['X']) < 1e-10

        # log(e) = 1
        result = prolog.query_once("X is log(2.718281828459045)")
        assert result is not None
        assert abs(result['X'] - 1.0) < 1e-10

    @pytest.mark.parametrize("input_val,expected", [
        (3.7, 3),
        (-3.7, -4),
        (5, 5),
    ])
    def test_floor(self, prolog, input_val, expected):
        """Test floor/1 with various values"""
        result = prolog.query_once(f"X is floor({input_val})")
        assert result is not None
        assert result['X'] == expected

    @pytest.mark.parametrize("input_val,expected", [
        (3.2, 4),
        (-3.2, -3),
        (5, 5),
    ])
    def test_ceiling(self, prolog, input_val, expected):
        """Test ceiling/1 with various values"""
        result = prolog.query_once(f"X is ceiling({input_val})")
        assert result is not None
        assert result['X'] == expected

    @pytest.mark.parametrize("input_val,expected", [
        (3.4, 3),
        (3.6, 4),
        (-3.4, -3),
        (-3.6, -4),
    ])
    def test_round(self, prolog, input_val, expected):
        """Test round/1 with various values"""
        result = prolog.query_once(f"X is round({input_val})")
        assert result is not None
        assert result['X'] == expected

    @pytest.mark.parametrize("input_val,expected", [
        (5, 1),
        (3.14, 1),
        (-5, -1),
        (-3.14, -1),
        (0, 0),
    ])
    def test_sign(self, prolog, input_val, expected):
        """Test sign/1 with various values"""
        result = prolog.query_once(f"X is sign({input_val})")
        assert result is not None
        assert result['X'] == expected

    def test_nested_math_functions(self, prolog):
        """Test nested math function calls"""
        # abs(min(-5, -3))
        result = prolog.query_once("X is abs(min(-5, -3))")
        assert result is not None
        assert result['X'] == 5

        # sqrt(abs(-16))
        result = prolog.query_once("X is sqrt(abs(-16))")
        assert result is not None
        assert result['X'] == 4.0

        # max(floor(3.7), ceiling(2.1))
        result = prolog.query_once("X is max(floor(3.7), ceiling(2.1))")
        assert result is not None
        assert result['X'] == 3

    def test_math_in_expressions(self, prolog):
        """Test math functions in arithmetic expressions"""
        # abs(-5) + abs(-3)
        result = prolog.query_once("X is abs(-5) + abs(-3)")
        assert result is not None
        assert result['X'] == 8

        # sqrt(16) * 2
        result = prolog.query_once("X is sqrt(16) * 2")
        assert result is not None
        assert result['X'] == 8.0

        # max(10, 20) - min(5, 3)
        result = prolog.query_once("X is max(10, 20) - min(5, 3)")
        assert result is not None
        assert result['X'] == 17
