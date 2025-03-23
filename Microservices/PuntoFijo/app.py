from flask import Flask, request, jsonify
from sympy import symbols, sqrt
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Transformaciones para permitir multiplicación implícita (por ejemplo, 2x en lugar de 2*x)
transformations = (standard_transformations + (implicit_multiplication_application,))

@app.route('/punto_fijo', methods=['GET'])
def metodo_punto_fijo():
    try:
        # Obtener los parámetros de la solicitud
        ecuacion_str = request.args.get('ecuacion')  # Ecuación original
        transformada_str = request.args.get('transformada')  # Función de iteración g(x)
        x0 = request.args.get('x0', type=float)  # Valor inicial
        tol_error = request.args.get('tol_error', type=float)  # Tolerancia de error

        # Validar que todos los parámetros estén presentes
        if not ecuacion_str or not transformada_str or x0 is None or tol_error is None:
            return jsonify({"error": "Debes proporcionar 'ecuacion', 'transformada', 'x0' y 'tol_error' en los parámetros de la URL."}), 400

        # Validar que la tolerancia de error esté en el rango permitido
        if tol_error < 1e-10 or tol_error > 0.999999:
            return jsonify({"error": "El valor de 'tol_error' debe estar entre 0.0000000001 y 0.999999."}), 400

        # Convertir la ecuación y la transformada a expresiones simbólicas
        x = symbols('x')
        try:
            ecuacion = parse_expr(ecuacion_str, transformations=transformations)
            transformada = parse_expr(transformada_str, transformations=transformations)
        except Exception as e:
            return jsonify({"error": f"Error en la sintaxis de la ecuación o transformada: {str(e)}"}), 400

        # Variables de iteración
        nIteracion = 0
        error = 1.0
        x_actual = x0
        tabla = []

        # Algoritmo de punto fijo
        while error >= tol_error:
            nIteracion += 1

            # Calcular el siguiente valor de x usando la función de iteración
            x_siguiente = float(transformada.subs(x, x_actual))

            # Calcular el error relativo
            if x_siguiente != 0:
                error = abs((x_siguiente - x_actual) / x_siguiente)
            else:
                error = 0  # Si x_siguiente es 0, evitamos división por 0

            # Calcular f(x_actual) para fines de visualización
            fxi = float(abs(ecuacion.subs(x, x_actual)))

            # Agregar la iteración a la tabla de resultados
            tabla.append({
                "nIteracion": nIteracion,
                "fxi": round(fxi, 4),  # Redondear a 4 decimales
                "x_actual": round(x_actual, 4),  # Redondear a 4 decimales
                "x_siguiente": round(x_siguiente, 4),  # Redondear a 4 decimales
                "error": round(float(error), 4)  # Redondear a 4 decimales
            })

            # Actualizar el valor de x para la siguiente iteración
            x_actual = x_siguiente

            # Verificar si el método no converge después de un número máximo de iteraciones
            if nIteracion >= 100:
                return jsonify({
                    "error": "El método no convergió después del número máximo de iteraciones.",
                    "tabla": tabla
                }), 400

        # Retornar la tabla de iteraciones
        return jsonify(tabla)

    except Exception as e:
        return jsonify({"error": f"Error inesperado: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)