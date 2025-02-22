from flask import Flask, request, jsonify
from sympy import symbols
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

app = Flask(__name__)

# Transformaciones para permitir multiplicación implícita (por ejemplo, 2x en lugar de 2*x)
transformations = (standard_transformations + (implicit_multiplication_application,))

@app.route('/biseccion', methods=['GET'])
def metodo_biseccion():
    # Obtener la ecuación, el intervalo [a, b] y la tolerancia del error desde la URL
    ecuacion_str = request.args.get('ecuacion')
    xo = request.args.get('xo', type=float)
    xu = request.args.get('xu', type=float)
    tol_error = request.args.get('tol_error', type=float)

    # Verificar que todos los parámetros estén presentes
    if not ecuacion_str or xo is None or xu is None or tol_error is None:
        return jsonify({"error": "Debes proporcionar 'ecuacion', 'xo', 'xu' y 'tol_error' en los parámetros de la URL"}), 400

    try:
        # Convertir la ecuación en una expresión simbólica
        x = symbols('x')
        ecuacion = parse_expr(ecuacion_str, transformations=transformations)

        # Inicializar variables
        nIteracion = 0
        error = 1.0
        panterior = 0
        pactual = 0

        # Lista para almacenar la tabla de iteraciones
        tabla = []

        # Verificar que el intervalo cumpla con f(xo) * f(xu) < 0
        fxo = ecuacion.subs(x, xo)
        fxu = ecuacion.subs(x, xu)

        if fxo * fxu >= 0:
            return jsonify({"error": "El intervalo [xo, xu] no cumple con f(xo) * f(xu) < 0."}), 400

        # Bucle del método de bisección
        while error >= tol_error:
            nIteracion += 1
            panterior = pactual
            xm = (xo + xu) / 2  # Punto medio
            fxm = ecuacion.subs(x, xm)  # Evaluar la función en xm
            fx1 = ecuacion.subs(x, xo)  # Evaluar la función en xo

            # Actualizar el intervalo
            if fx1 * fxm < 0:
                aux=xo
                aux1=xu
                xu = xm
            else:
                aux=xo
                aux1=xu
                xo = xm

            # Calcular el error
            pactual = xm
            error = abs((pactual - panterior) / pactual)

            # Agregar los datos de la iteración a la tabla
            tabla.append({
                "nIteracion": nIteracion,
                "xo": aux,
                "xu": aux1,
                "xm": xm,
                "fxm": float(fxm),
                "error": float(error)
            })

        # Retornar la tabla de iteraciones
        return jsonify(tabla)

    except Exception as e:
        return jsonify({"error": f"Error al procesar la ecuación: {str(e)}"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)