#CALCULATOR

import ast
import math
import operator as op
import streamlit as st
from datetime import datetime

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Advanced Scientific Calculator",
    page_icon="🧮",
    layout="centered",
    initial_sidebar_state="expanded"
)

# =========================================================
# PROFESSIONAL DARK THEME
# =========================================================

st.markdown("""
<style>
.stApp {
    background: linear-gradient(145deg, #0b1020, #18263b);
    color: #f1f5f9;
}

.block-container {
    max-width: 850px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

.calculator-title {
    text-align: center;
    font-size: 38px;
    font-weight: 800;
    color: #64d8cb;
    margin-bottom: 5px;
}

.subtitle {
    text-align: center;
    color: #a6b5cc;
    margin-bottom: 25px;
}

.display-box {
    background: #080d19;
    border: 1px solid #34445e;
    border-radius: 18px;
    padding: 22px;
    margin: 12px 0 18px 0;
    overflow-wrap: anywhere;
}

.expression-text {
    color: #9baec8;
    font-size: 15px;
    text-align: right;
    min-height: 24px;
}

.result-text {
    color: #64d8cb;
    font-size: 38px;
    font-weight: 750;
    text-align: right;
    min-height: 48px;
}

div.stButton > button {
    width: 100%;
    min-height: 51px;
    border-radius: 11px;
    border: 1px solid #3a4b65;
    background: #24334a;
    color: #f1f5f9;
    font-size: 17px;
    font-weight: 650;
    transition: all 0.15s ease;
}

div.stButton > button:hover {
    background: #354b68;
    border-color: #64d8cb;
    color: #64d8cb;
}

div[data-testid="stTextInput"] input {
    background: #101a2b;
    color: #64d8cb;
    border: 1px solid #425573;
    border-radius: 10px;
}

section[data-testid="stSidebar"] {
    background: #101827;
}

.history-item {
    background: #172438;
    border: 1px solid #2e405a;
    border-radius: 10px;
    padding: 10px;
    margin-bottom: 8px;
    overflow-wrap: anywhere;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# SESSION STATE
# =========================================================

defaults = {
    "expression_input": "",
    "result": "0",
    "last_answer": 0.0,
    "history": [],
    "angle_mode": "Degrees",
    "just_calculated": False,
    "error_message": ""
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# =========================================================
# SAFE MATHEMATICAL EXPRESSION EVALUATOR
# Does not use Python eval()
# =========================================================

class CalculatorError(Exception):
    pass


def safe_calculate(expression, angle_mode, answer):
    expression = expression.strip()

    if not expression:
        raise CalculatorError("Enter a mathematical expression.")

    if len(expression) > 250:
        raise CalculatorError("Expression is too long.")

    # Allow only calculator characters and known names.
    allowed_names = {
        "sqrt", "sin", "cos", "tan",
        "asin", "acos", "atan",
        "log", "ln", "log2", "log10",
        "abs", "fact", "floor", "ceil",
        "exp", "pi", "e", "ans"
    }

    try:
        tree = ast.parse(expression, mode="eval")
    except (SyntaxError, ValueError):
        raise CalculatorError("Invalid expression. Check your syntax.")

    def factorial(value):
        if value < 0 or not float(value).is_integer():
            raise CalculatorError(
                "Factorial requires a non-negative integer."
            )
        if value > 170:
            raise CalculatorError("Factorial is limited to 170.")
        return math.factorial(int(value))

    def trig_input(value):
        if angle_mode == "Degrees":
            return math.radians(value)
        return value

    def inverse_trig(value):
        if angle_mode == "Degrees":
            return math.degrees(value)
        return value

    functions = {
        "sqrt": math.sqrt,
        "sin": lambda x: math.sin(trig_input(x)),
        "cos": lambda x: math.cos(trig_input(x)),
        "tan": lambda x: math.tan(trig_input(x)),
        "asin": lambda x: inverse_trig(math.asin(x)),
        "acos": lambda x: inverse_trig(math.acos(x)),
        "atan": lambda x: inverse_trig(math.atan(x)),
        "log": math.log10,
        "log10": math.log10,
        "log2": math.log2,
        "ln": math.log,
        "abs": abs,
        "fact": factorial,
        "floor": math.floor,
        "ceil": math.ceil,
        "exp": math.exp
    }

    binary_ops = {
        ast.Add: op.add,
        ast.Sub: op.sub,
        ast.Mult: op.mul,
        ast.Div: op.truediv,
        ast.Mod: op.mod,
        ast.Pow: op.pow
    }

    unary_ops = {
        ast.UAdd: op.pos,
        ast.USub: op.neg
    }

    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)

        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)) and not isinstance(
                node.value, bool
            ):
                return node.value
            raise CalculatorError("Only numeric values are allowed.")

        if isinstance(node, ast.Name):
            constants = {
                "pi": math.pi,
                "e": math.e,
                "ans": answer
            }

            if node.id in constants:
                return constants[node.id]

            raise CalculatorError(
                f"Unknown name: {node.id}. Check the function name."
            )

        if isinstance(node, ast.BinOp):
            operation = binary_ops.get(type(node.op))

            if operation is None:
                raise CalculatorError("Unsupported operation.")

            left = evaluate(node.left)
            right = evaluate(node.right)

            if isinstance(node.op, ast.Pow):
                if abs(right) > 1000:
                    raise CalculatorError(
                        "Exponent is too large (maximum magnitude 1000)."
                    )

            result = operation(left, right)

            if isinstance(result, complex):
                raise CalculatorError(
                    "Complex-number results are not supported."
                )

            if not math.isfinite(float(result)):
                raise CalculatorError("Result is outside the supported range.")

            return result

        if isinstance(node, ast.UnaryOp):
            operation = unary_ops.get(type(node.op))

            if operation is None:
                raise CalculatorError("Unsupported unary operation.")

            return operation(evaluate(node.operand))

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise CalculatorError("Unsupported function call.")

            name = node.func.id

            if name not in allowed_names or name not in functions:
                raise CalculatorError(f"Unsupported function: {name}")

            if node.keywords or len(node.args) != 1:
                raise CalculatorError(
                    f"{name}() requires exactly one argument."
                )

            argument = evaluate(node.args[0])
            return functions[name](argument)

        raise CalculatorError("This expression contains unsupported syntax.")

    try:
        result = evaluate(tree)

        if isinstance(result, complex) or not math.isfinite(float(result)):
            raise CalculatorError("Result is outside the supported range.")

        return result

    except CalculatorError:
        raise
    except ZeroDivisionError:
        raise CalculatorError("Cannot divide by zero.")
    except OverflowError:
        raise CalculatorError("The result is too large.")
    except (ValueError, TypeError):
        raise CalculatorError(
            "Invalid mathematical input. Check the function and its argument."
        )

# =========================================================
# RESULT FORMATTING
# =========================================================

def format_result(value):
    value = float(value)

    if not math.isfinite(value):
        return str(value)

    if value == 0:
        return "0"

    if value.is_integer() and abs(value) < 1e15:
        return f"{int(value):,}"

    return f"{value:,.12g}"


# =========================================================
# CALCULATOR CALLBACKS
# =========================================================

def press_key(key):
    current = st.session_state.expression_input
    st.session_state.error_message = ""

    if key == "C":
        st.session_state.expression_input = ""
        st.session_state.result = "0"
        st.session_state.just_calculated = False
        return

    if key == "⌫":
        st.session_state.expression_input = current[:-1]
        st.session_state.just_calculated = False
        return

    if key == "=":
        run_calculation()
        return

    if key == "Ans":
        value = "ans"
    elif key == "π":
        value = "pi"
    elif key == "√":
        value = "sqrt("
    elif key == "x²":
        value = "**2"
    elif key == "xʸ":
        value = "**"
    elif key == "x!":
        value = "fact("
    elif key in ("sin", "cos", "tan", "asin", "acos", "atan",
                 "log", "ln", "log2", "log10", "abs", "exp",
                 "floor", "ceil"):
        value = key + "("
    elif key == "×":
        value = "*"
    elif key == "÷":
        value = "/"
    elif key == "−":
        value = "-"
    elif key == "mod":
        value = "%"
    elif key == "e":
        value = "e"
    else:
        value = key

    # After a result, digits start a fresh calculation.
    # Operators continue from the previous answer.
    if st.session_state.just_calculated:
        if key in "0123456789." and len(key) == 1:
            current = ""
        elif key in ("π", "e", "√", "sin", "cos", "tan",
                     "asin", "acos", "atan", "log", "ln",
                     "log2", "log10", "abs", "exp", "floor",
                     "ceil", "x!", "("):
            current = ""
        elif key in ("+", "−", "-", "×", "*", "÷", "/", "mod",
                     "x²", "xʸ"):
            current = st.session_state.result.replace(",", "")
        st.session_state.just_calculated = False

    st.session_state.expression_input = current + value


def run_calculation():
    expression = st.session_state.expression_input.strip()

    try:
        result = safe_calculate(
            expression,
            st.session_state.angle_mode,
            st.session_state.last_answer
        )

        formatted = format_result(result)
        st.session_state.result = formatted
        st.session_state.last_answer = result
        st.session_state.error_message = ""
        st.session_state.just_calculated = True

        st.session_state.history.insert(
            0,
            {
                "expression": expression,
                "result": formatted,
                "time": datetime.now().strftime("%H:%M:%S")
            }
        )

        # Keep the most recent 50 calculations.
        st.session_state.history = st.session_state.history[:50]

    except CalculatorError as error:
        st.session_state.error_message = str(error)
    except Exception:
        st.session_state.error_message = (
            "Unable to calculate this expression. Check your input."
        )

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.title("⚙️ Calculator Settings")

    st.session_state.angle_mode = st.radio(
        "Trigonometry angle mode",
        ["Degrees", "Radians"],
        index=0 if st.session_state.angle_mode == "Degrees" else 1
    )

    st.caption(
        "Examples: sin(30), sqrt(81), log(100), "
        "fact(5), pi, e, ans"
    )

    st.divider()
    st.subheader("🕘 Calculation History")

    if not st.session_state.history:
        st.caption("Your calculations will appear here.")

    for index, item in enumerate(st.session_state.history):
        st.markdown(
            f"""
            <div class="history-item">
                <small>{item["time"]}</small><br>
                <span>{item["expression"]}</span><br>
                <strong style="color:#64d8cb">
                    = {item["result"]}
                </strong>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "Use result",
            key=f"use_history_{index}",
            use_container_width=True
        ):
            st.session_state.expression_input = item["result"].replace(",", "")
            st.session_state.just_calculated = False
            st.rerun()

    if st.session_state.history:
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.history = []
            st.rerun()

# =========================================================
# MAIN INTERFACE
# =========================================================

st.markdown(
    '<div class="calculator-title">🧮 Scientific Calculator</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Advanced calculations • Python • Streamlit</div>',
    unsafe_allow_html=True
)

st.markdown(
    f"""
    <div class="display-box">
        <div class="expression-text">
            {st.session_state.expression_input or "Ready to calculate"}
        </div>
        <div class="result-text">{st.session_state.result}</div>
    </div>
    """,
    unsafe_allow_html=True
)

st.text_input(
    "Expression",
    key="expression_input",
    placeholder="Example: (7 + 3) * sqrt(81)"
)

st.caption(
    "Type an expression above or use the buttons. "
    "Use * for multiplication and / for division."
)

if st.button("＝  Calculate", use_container_width=True, type="primary"):
    run_calculation()

if st.session_state.error_message:
    st.error(st.session_state.error_message)

st.divider()

# =========================================================
# SCIENTIFIC KEYPAD
# =========================================================

keypad = [
    ["C", "⌫", "(", ")", "mod"],
    ["sin", "cos", "tan", "√", "x²"],
    ["asin", "acos", "atan", "xʸ", "x!"],
    ["log", "ln", "log2", "log10", "exp"],
    ["7", "8", "9", "÷", "π"],
    ["4", "5", "6", "×", "e"],
    ["1", "2", "3", "−", "Ans"],
    ["0", ".", "±", "+", "="]
]

for row_index, row in enumerate(keypad):
    columns = st.columns(len(row))

    for column, key in zip(columns, row):
        with column:
            if key == "±":
                # Insert a unary minus; use parentheses for clarity.
                if st.button(key, key=f"key_{row_index}_{key}",
                             use_container_width=True):
                    current = st.session_state.expression_input
                    st.session_state.error_message = ""

                    if current and not st.session_state.just_calculated:
                        st.session_state.expression_input = f"-({current})"
                    elif st.session_state.just_calculated:
                        st.session_state.expression_input = (
                            f"-({st.session_state.result.replace(',', '')})"
                        )
                        st.session_state.just_calculated = False
                    else:
                        st.session_state.expression_input = "-"

                    st.rerun()
            else:
                st.button(
                    key,
                    key=f"key_{row_index}_{key}",
                    use_container_width=True,
                    on_click=press_key,
                    args=(key,)
                )

st.divider()

st.markdown("#### Quick examples")

examples = [
    "sqrt(144)",
    "sin(30)",
    "log(100)",
    "fact(5)",
    "(7 + 3) * 8",
    "2**10"
]

example_columns = st.columns(3)

for index, example in enumerate(examples):
    with example_columns[index % 3]:
        if st.button(
            example,
            key=f"example_{index}",
            use_container_width=True
        ):
            st.session_state.expression_input = example
            st.session_state.error_message = ""
            st.session_state.just_calculated = False
            st.rerun()

st.markdown("---")
st.caption(
    "Built with Python and Streamlit • "
    "Expressions are evaluated using a restricted mathematical parser."
)