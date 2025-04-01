from flask import Flask, request, jsonify
import numpy as np
import json
import urllib.parse
from sympy import symbols, Eq, parse_expr, linear_eq_to_matrix
from sympy.parsing.sympy_parser import standard_transformations, implicit_multiplication_application
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Transformaciones para el parser de ecuaciones
transformations = (standard_transformations + (implicit_multiplication_application,))

def decode_equation(eq):
    """Decodifica la ecuación reemplazando %3D por = y otros caracteres especiales"""
    decoded = urllib.parse.unquote(eq)  # Decodifica %3D a =
    decoded = decoded.replace(" ", "")  # Elimina espacios
    return decoded

def reordenar_ecuaciones(sym_ecuaciones, variables):
    """
    Reordena las ecuaciones para evitar ceros en la diagonal y mejorar la dominancia diagonal.
    Devuelve las ecuaciones reordenadas y las variables en el nuevo orden.
    """
    # Convertir a matriz para análisis
    sym_vars = symbols(variables)
    A_sym, _ = linear_eq_to_matrix([eq.lhs - eq.rhs for eq in sym_ecuaciones], sym_vars)
    A = np.array(A_sym, dtype=float)
    
    n = len(variables)
    nuevo_orden = []
    ecuaciones_disponibles = list(range(n))
    variables_disponibles = list(range(n))
    
    # Primera pasada: asegurar elementos no cero en la diagonal
    for i in range(n):
        mejor_ecuacion = None
        mejor_puntaje = -1
        
        for eq_idx in ecuaciones_disponibles:
            for var_idx in variables_disponibles:
                if A[eq_idx, var_idx] != 0:
                    # Puntaje basado en dominancia diagonal
                    puntaje = abs(A[eq_idx, var_idx]) - sum(abs(A[eq_idx, j]) for j in range(n) if j != var_idx)
                    
                    if puntaje > mejor_puntaje:
                        mejor_puntaje = puntaje
                        mejor_ecuacion = eq_idx
                        mejor_variable = var_idx
        
        if mejor_ecuacion is None:
            raise ValueError("No se puede reordenar el sistema para evitar ceros en la diagonal")
            
        nuevo_orden.append((mejor_ecuacion, mejor_variable))
        ecuaciones_disponibles.remove(mejor_ecuacion)
        variables_disponibles.remove(mejor_variable)
    
    # Reordenar ecuaciones y variables según el nuevo orden
    ecuaciones_ordenadas = [sym_ecuaciones[eq_idx] for eq_idx, _ in nuevo_orden]
    variables_ordenadas = [variables[var_idx] for _, var_idx in nuevo_orden]
    
    return ecuaciones_ordenadas, variables_ordenadas

@app.route('/jacobi', methods=['GET', 'POST'])
def metodo_jacobi():
    try:
        # Obtener parámetros según el método HTTP usado
        if request.method == 'POST':
            data = request.get_json()
            ecuaciones = data.get('ecuaciones', [])
            x0_str = data.get('x0')
            tol_error = data.get('tol_error')
            max_iter = data.get('max_iter', 100)
        else:
            # Para GET, decodificar cada ecuación
            ecuaciones = [decode_equation(eq) for eq in request.args.getlist('ecuaciones[]')]
            x0_str = request.args.get('x0')
            tol_error = request.args.get('tol_error', type=float)
            max_iter = request.args.get('max_iter', type=int, default=100)

        # Validar parámetros mínimos
        if not ecuaciones or not x0_str or tol_error is None:
            return jsonify({"error": "Debes proporcionar 'ecuaciones', 'x0' y 'tol_error'."}), 400

        # Procesar ecuaciones
        try:
            sym_ecuaciones = []
            for eq in ecuaciones:
                if "=" not in eq:
                    return jsonify({"error": f"La ecuación '{eq}' no contiene '='."}), 400
                lado_izq, lado_der = eq.split("=", 1)  # Split en el primer = solamente
                expr_izq = parse_expr(lado_izq, transformations=transformations)
                expr_der = parse_expr(lado_der, transformations=transformations)
                sym_ecuaciones.append(Eq(expr_izq, expr_der))
            
            # Extraer variables iniciales
            variables = sorted(set().union(*[eq.free_symbols for eq in sym_ecuaciones]), key=lambda v: str(v))
            variables = [str(var) for var in variables]
            
            # Reordenar ecuaciones para evitar ceros en la diagonal
            sym_ecuaciones, variables = reordenar_ecuaciones(sym_ecuaciones, variables)
        except Exception as e:
            return jsonify({"error": f"Error al procesar ecuaciones: {str(e)}"}), 400

        # Convertir y validar vector inicial
        try:
            x0 = np.array(json.loads(x0_str), dtype=float)
            if len(x0) != len(variables):
                return jsonify({"error": "El tamaño del vector inicial no coincide con el número de variables."}), 400
        except Exception as e:
            return jsonify({"error": f"Error en el vector inicial: {str(e)}"}), 400

        # Convertir a forma matricial
        try:
            sym_vars = symbols(variables)
            A_sym, b_sym = linear_eq_to_matrix([eq.lhs - eq.rhs for eq in sym_ecuaciones], sym_vars)
            A = np.array(A_sym, dtype=float)
            b = np.array(b_sym, dtype=float).flatten()
        except Exception as e:
            return jsonify({"error": f"Error al convertir a matriz: {str(e)}"}), 400

        # Verificar dominancia diagonal
        es_diagonal_dominante = all(2 * abs(A[i, i]) >= np.sum(np.abs(A[i, :])) for i in range(A.shape[0]))
        advertencia = None if es_diagonal_dominante else "Advertencia: La matriz no es estrictamente diagonal dominante, la convergencia no está garantizada"

        # Algoritmo de Jacobi
        n = len(b)
        x = x0.copy()
        tabla = []

        for iteracion in range(max_iter):
            x_nuevo = np.zeros_like(x)
            for i in range(n):
                suma = np.dot(A[i, :], x) - A[i, i] * x[i]
                if A[i, i] == 0:
                    return jsonify({
                        "error": f"División por cero en la diagonal (A[{i}, {i}] = 0).",
                        "sugerencia": "Intente reordenar las ecuaciones manualmente o use otro método numérico."
                    }), 400
                
                x_nuevo[i] = (b[i] - suma) / A[i, i]

            error = np.linalg.norm(x_nuevo - x, ord=np.inf)
            residuo = np.linalg.norm(np.dot(A, x_nuevo) - b, ord=np.inf)
            
            # Guardar resultados de la iteración
            tabla.append({
                "iteracion": iteracion + 1,
                "valores": {var: float(x_nuevo[i]) for i, var in enumerate(variables)},
                "error": float(error),
                "residuo": float(residuo)
            })

            if error < tol_error:
                return jsonify({
                    "convergio": True,
                    "iteraciones": iteracion + 1,
                    "error_final": float(error),
                    "residuo_final": float(residuo),
                    "solucion": {var: float(x_nuevo[i]) for i, var in enumerate(variables)},
                    "variables": variables,
                    "matriz_A": A.tolist(),
                    "vector_b": b.tolist(),
                    "tabla": tabla,
                    "advertencia": advertencia,
                    "diagonal_dominante": es_diagonal_dominante
                })
                
            x = x_nuevo.copy()

        return jsonify({
            "convergio": False,
            "iteraciones": max_iter,
            "error_final": float(error),
            "residuo_final": float(residuo),
            "solucion": None,
            "variables": variables,
            "matriz_A": A.tolist(),
            "vector_b": b.tolist(),
            "tabla": tabla,
            "advertencia": advertencia,
            "diagonal_dominante": es_diagonal_dominante
        })

    except Exception as e:
        return jsonify({"error": f"Error inesperado: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)