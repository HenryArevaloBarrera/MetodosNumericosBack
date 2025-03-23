from flask import Flask, request, jsonify
from sympy import symbols
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Transformaciones para permitir multiplicación implícita (por ejemplo, 2x en lugar de 2*x)
transformations = (standard_transformations + (implicit_multiplication_application,))

@app.route('/biseccion', methods=['GET'])
def metodo_biseccion():
    try:
        # Obtener los parámetros de la solicitud
        ecuacion_str = request.args.get('ecuacion')
        xo = request.args.get('xo', type=float)
        xu = request.args.get('xu', type=float)
        tol_error = request.args.get('tol_error', type=float)

        # Validar que todos los parámetros estén presentes
        if ecuacion_str is None or xo is None or xu is None or tol_error is None:
            return jsonify({"error": "Debes proporcionar 'ecuacion', 'xo', 'xu' y 'tol_error' en los parámetros de la URL."}), 400

        # Validar que el intervalo sea correcto
        if xo >= xu:
            return jsonify({"error": "El valor de 'xo' debe ser menor que 'xu'."}), 400

        # Validar que la tolerancia de error esté en el rango permitido
        if tol_error < 1e-10 or tol_error > 0.999999:
            return jsonify({"error": "El valor de 'tol_error' debe estar entre 0.0000000001 y 0.999999."}), 400

        # Convertir la ecuación a una expresión simbólica
        x = symbols('x')
        try:
            ecuacion = parse_expr(ecuacion_str, transformations=transformations)
        except Exception as e:
            return jsonify({"error": f"Error en la sintaxis de la ecuación: {str(e)}"}), 400

        # Evaluar f(xo) y f(xu) para verificar si el intervalo es válido
        try:
            fxo = ecuacion.subs(x, xo)
            fxu = ecuacion.subs(x, xu)
        except Exception as e:
            return jsonify({"error": f"Error al evaluar la ecuación: {str(e)}"}), 400

        if fxo * fxu >= 0:
            return jsonify({"error": "En el intervalo [xo, xu] no se encuentra la raiz de la ecuacion "}), 400

        # Variables de iteración
        nIteracion = 0
        error = 0.99
        panterior = 0
        pactual = 0
        tabla = []

        # Algoritmo de bisección
        while error >= tol_error:
            nIteracion += 1
            panterior = pactual
            xm = (xo + xu) / 2  # Punto medio
            fxm = ecuacion.subs(x, xm)  # Evaluar la función en xm

            # Guardar los valores previos de xo y xu
            aux_xo, aux_xu = xo, xu

            # Actualizar el intervalo
            if ecuacion.subs(x, xo) * fxm < 0:
                xu = xm
            else:
                xo = xm

            # Calcular el error con prevención de división por cero
            pactual = xm
            if pactual != 0:
                error = abs((pactual - panterior) / pactual)
            else:
                error = 0  # Si pactual es 0, evitamos división por 0

            # Agregar la iteración a la tabla de resultados
            tabla.append({
                "nIteracion": nIteracion,
                "xo": aux_xo,
                "xu": aux_xu,
                "xm": xm,
                "fxm": float(fxm),
                "error": float(error)
            })

        # Retornar la tabla de iteraciones
        return jsonify(tabla)

    except Exception as e:
        return jsonify({"error": f"Error inesperado: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
