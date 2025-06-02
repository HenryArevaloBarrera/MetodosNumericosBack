from flask import Flask, request, jsonify
from sympy import symbols, diff, N
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
from flask_cors import CORS
import numpy as np

app = Flask(__name__)
CORS(app)

transformations = (standard_transformations + (implicit_multiplication_application,))

@app.route('/newton_raphson', methods=['GET'])
def metodo_newton_raphson():
    try:
        # Obtener los parámetros de la solicitud
        ecuacion_str = request.args.get('ecuacion')  # Ecuación original f(x)
        x0 = request.args.get('x0', type=float)  # Valor inicial
        tol_error = request.args.get('tol_error', type=float)  # Tolerancia de error

        # Validar que todos los parámetros estén presentes
        if not ecuacion_str or x0 is None or tol_error is None:
            return jsonify({"error": "Debes proporcionar 'ecuacion', 'x0' y 'tol_error' en los parámetros de la URL."}), 400

        # Validar que la tolerancia de error esté en el rango permitido
        if tol_error < 1e-10 or tol_error > 0.999999:
            return jsonify({"error": "El valor de 'tol_error' debe estar entre 0.0000000001 y 0.999999."}), 400

        # Convertir la ecuación a expresión simbólica
        x = symbols('x')
        try:
            f = parse_expr(ecuacion_str, transformations=transformations)  # f(x)
            f_prima = diff(f, x)  # f'(x)
            g = x - ((f / f_prima))  # g(x) = x - f(x)/f'(x)
            g_prima = diff(g, x)  # g'(x)
        except Exception as e:
            return jsonify({"error": f"Error en la sintaxis de la ecuación: {str(e)}"}), 400

        # Mostrar por consola la ecuación g(x) y su derivada g'(x)
        print(f)
        print(f_prima)
        print("Ecuación g(x):", g)
        print("Derivada g'(x):", g_prima)

        # Variables de iteración
        nIteracion = 0
        error = 1.0
        x_actual = x0
        tabla = []
        x_hist = [x0]
        fx_hist = [float(N(f.subs(x, x0)))]

        # Algoritmo de Newton-Raphson
        while error >= tol_error:
            nIteracion += 1

            try:
                # Calcular el siguiente valor de x usando g(x)
                x_siguiente = float(g.subs(x, x_actual))

                # Calcular el error absoluto
                error = abs(x_siguiente - x_actual)

                # Calcular f(x_actual) y g'(x_actual) para fines de visualización
                fxi = float(f.subs(x, x_actual))
                g_prima_valor = float(g_prima.subs(x, x_actual))

                # Agregar la iteración a la tabla de resultados
                tabla.append({
                    "nIteracion": nIteracion,
                    "xi": round(x_actual, 4),  # Redondear a 4 decimales
                    "fxi": round(fxi, 4),  # Redondear a 4 decimales
                    "g_prima": round(g_prima_valor, 4),  # Redondear a 4 decimales
                    "error": round(error, 4)  # Redondear a 4 decimales
                })

                # Guardar historial para gráfica
                x_hist.append(x_siguiente)
                fx_hist.append(float(N(f.subs(x, x_siguiente))))

                # Actualizar el valor de x para la siguiente iteración
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

        # Para la gráfica: evaluamos f(x) en un rango que cubra todos los valores de x_hist
        min_x = min(x_hist)
        max_x = max(x_hist)
        if min_x == max_x:
            min_x -= 1
            max_x += 1
        grafico_x = np.linspace(min_x, max_x, 100)
        grafico_y = []
        for val in grafico_x:
            try:
                yval = float(N(f.subs(x, val)))
            except:
                yval = None
            grafico_y.append(yval)

        # Retornar la tabla de iteraciones y la gráfica
        return jsonify({
            "tabla": tabla,
            "grafico_x": grafico_x.tolist(),
            "grafico_y": grafico_y,
            "x_hist": x_hist,
            "fx_hist": fx_hist
        })

    except Exception as e:
        return jsonify({"error": f"Error inesperado: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)