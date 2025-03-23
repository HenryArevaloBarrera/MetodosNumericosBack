from flask import Flask, request, jsonify
from sympy import symbols, diff
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

transformations = (standard_transformations + (implicit_multiplication_application,))

@app.route('/secante', methods=['GET'])
def metodo_secante():
    try:
        # Obtener los parámetros de la solicitud
        ecuacion_str = request.args.get('ecuacion')  # Ecuación original f(x)
        x0 = request.args.get('x0', type=float)  # Primer valor inicial
        x1 = request.args.get('x1', type=float)  # Segundo valor inicial
        tol_error = request.args.get('tol_error', type=float)  # Tolerancia de error

        # Validar que todos los parámetros estén presentes
        if not ecuacion_str or x0 is None or x1 is None or tol_error is None:
            return jsonify({"error": "Debes proporcionar 'ecuacion', 'x0', 'x1' y 'tol_error' en los parámetros de la URL."}), 400

        # Validar que la tolerancia de error esté en el rango permitido
        if tol_error < 1e-10 or tol_error > 0.999999:
            return jsonify({"error": "El valor de 'tol_error' debe estar entre 0.0000000001 y 0.999999."}), 400

        # Convertir la ecuación a expresión simbólica
        x = symbols('x')
        try:
            f = parse_expr(ecuacion_str, transformations=transformations)  # f(x)
        except Exception as e:
            return jsonify({"error": f"Error en la sintaxis de la ecuación: {str(e)}"}), 400

        # Variables de iteración
        nIteracion = 0
        error = 1.0
        x_actual = x0
        x_anterior = x1
        tabla = []

        # Algoritmo de la secante
        while error >= tol_error:
            nIteracion += 1

            try:
                # Calcular f(x_actual) y f(x_anterior)
                f_actual = float(f.subs(x, x_actual))
                f_anterior = float(f.subs(x, x_anterior))

                # Calcular el siguiente valor de x usando la fórmula de la secante
                x_siguiente = x_actual - (f_actual * (x_actual - x_anterior)) / (f_actual - f_anterior)

                # Calcular el error absoluto
                error = abs(x_siguiente - x_actual)

                # Calcular f(x_siguiente) para fines de visualización
                f_siguiente = float(f.subs(x, x_siguiente))

                # Agregar la iteración a la tabla de resultados
                tabla.append({
                    "nIteracion": nIteracion,
                    "x_actual": round(x_actual, 4),  # Redondear a 4 decimales
                    "x_anterior": round(x_anterior, 4),  # Redondear a 4 decimales
                    "x_siguiente": round(x_siguiente, 4),  # Redondear a 4 decimales
                    "f_siguiente": round(f_siguiente, 4),  # Redondear a 4 decimales
                    "error": round(error, 4)  # Redondear a 4 decimales
                })

                # Actualizar los valores de x para la siguiente iteración
                x_anterior = x_actual
                x_actual = x_siguiente

                # Verificar si el método no converge después de un número máximo de iteraciones
                if nIteracion >= 100:
                    return jsonify({
                        "error": "El método no convergió después del número máximo de iteraciones.",
                        "tabla": tabla
                    }), 400

            except ZeroDivisionError:
                return jsonify({"error": "División por cero encontrada. El método no puede continuar."}), 400
            except Exception as e:
                return jsonify({"error": f"Error durante la iteración: {str(e)}"}), 400

        # Retornar la tabla de iteraciones
        return jsonify(tabla)

    except Exception as e:
        return jsonify({"error": f"Error inesperado: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004)