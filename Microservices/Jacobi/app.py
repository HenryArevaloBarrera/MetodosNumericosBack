from flask import Flask, request, jsonify
import numpy as np
import json
from sympy import symbols, Eq, parse_expr, linear_eq_to_matrix
from sympy.parsing.sympy_parser import standard_transformations, implicit_multiplication_application
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Transformaciones para el parser de ecuaciones
transformations = (standard_transformations + (implicit_multiplication_application,))

@app.route('/jacobi', methods=['GET', 'POST'])
def metodo_jacobi():
    try:
        # Depuración: Mostrar el método HTTP y los parámetros recibidos
        print(f"Método HTTP: {request.method}")
        print(f"Parámetros recibidos: {request.args if request.method == 'GET' else request.get_json()}")

        # Obtener parámetros según el método HTTP usado
        if request.method == 'POST':
            data = request.get_json()
            ecuaciones = data.get('ecuaciones', [])
            x0_str = data.get('x0')
            tol_error = data.get('tol_error')
            max_iter = data.get('max_iter', 100)
        else:
            ecuaciones = request.args.getlist('ecuaciones[]')  # Usar 'ecuaciones[]' para GET
            x0_str = request.args.get('x0')
            tol_error = request.args.get('tol_error', type=float)
            max_iter = request.args.get('max_iter', type=int, default=100)

        # Depuración: Mostrar los parámetros obtenidos
        print(f"Ecuaciones: {ecuaciones}")
        print(f"x0: {x0_str}")
        print(f"Tolerancia: {tol_error}")
        print(f"Máximo de iteraciones: {max_iter}")

        # Validar que se hayan enviado los parámetros mínimos
        if not ecuaciones or not x0_str or tol_error is None:
            return jsonify({"error": "Debes proporcionar 'ecuaciones', 'x0' y 'tol_error'."}), 400

        # Procesar las ecuaciones y separar lado izquierdo y derecho
        try:
            sym_ecuaciones = []
            for eq in ecuaciones:
                if "=" not in eq:
                    return jsonify({"error": f"La ecuación '{eq}' no contiene '='."}), 400
                lado_izq, lado_der = eq.split("=")
                expr_izq = parse_expr(lado_izq.replace(" ", ""), transformations=transformations)
                expr_der = parse_expr(lado_der.replace(" ", ""), transformations=transformations)
                sym_ecuaciones.append(Eq(expr_izq, expr_der))
            # Extraer variables automáticamente y ordenarlas
            variables = sorted(set().union(*[eq.free_symbols for eq in sym_ecuaciones]), key=lambda v: str(v))
            variables = [str(var) for var in variables]
        except Exception as e:
            return jsonify({"error": f"Error al analizar las ecuaciones: {str(e)}"}), 400

        # Convertir el vector inicial a un array NumPy
        try:
            x0 = np.array(json.loads(x0_str), dtype=float)
        except Exception as e:
            return jsonify({"error": f"Error en la sintaxis del vector inicial x0: {str(e)}"}), 400

        # Validar que el número de ecuaciones coincida con el número de variables
        if len(ecuaciones) != len(variables):
            return jsonify({
                "error": "El número de ecuaciones debe ser igual al número de variables.",
                "detalle": f"Número de ecuaciones: {len(ecuaciones)}, Número de variables: {len(variables)}"
            }), 400

        # Convertir las ecuaciones a la forma matricial Ax = b
        try:
            sym_vars = symbols(variables)
            A_sym, b_sym = linear_eq_to_matrix([eq.lhs - eq.rhs for eq in sym_ecuaciones], sym_vars)
            A = np.array(A_sym, dtype=float)
            b = np.array(b_sym, dtype=float).flatten()
        except Exception as e:
            return jsonify({"error": f"Error al convertir las ecuaciones a matriz: {str(e)}"}), 400

        # Validar dimensiones de A, b y x0
        if A.shape[0] != A.shape[1] or A.shape[0] != b.shape[0] or b.shape[0] != x0.shape[0]:
            return jsonify({"error": "Las dimensiones de la matriz A, el vector b y el vector x0 no coinciden."}), 400

        # Verificar si la matriz es diagonalmente dominante
        diagonal_dominante = all(2 * abs(A[i, i]) >= np.sum(np.abs(A[i, :])) for i in range(A.shape[0]))
        if not diagonal_dominante:
            return jsonify({"error": "La matriz no es diagonalmente dominante. El método de Jacobi puede no converger."}), 400

        # Algoritmo de Jacobi
        n = len(b)
        x = x0.copy()
        tabla = []

        for iteracion in range(max_iter):
            x_nuevo = np.zeros_like(x)
            for i in range(n):
                # Sumar A[i,j] * x[j] para j != i
                suma = np.dot(A[i, :], x) - A[i, i] * x[i]
                if A[i, i] == 0:
                    return jsonify({"error": f"División por cero en la diagonal (A[{i}, {i}] = 0)."}), 400
                x_nuevo[i] = (b[i] - suma) / A[i, i]

            error = np.linalg.norm(x_nuevo - x, ord=np.inf)
            tabla.append({
                "iteracion": iteracion + 1,
                "x": [round(val, 4) for val in x_nuevo],
                "error": round(error, 4)
            })
            if error < tol_error:
                return jsonify({"tabla": tabla, "mensaje": "Convergencia alcanzada"})
            x = x_nuevo.copy()

        return jsonify({"tabla": tabla, "mensaje": "No se alcanzó la convergencia en el número máximo de iteraciones"})

    except Exception as e:
        return jsonify({"error": f"Error inesperado: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)