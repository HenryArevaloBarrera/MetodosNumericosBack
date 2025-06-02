from flask import Flask, request, jsonify
from sympy import symbols, integrate, N
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Transformaciones para permitir multiplicación implícita
transformations = (standard_transformations + (implicit_multiplication_application,))

@app.route('/simpson', methods=['GET'])
def metodo_simpson():
    try:
        # Obtener parámetros
        ecuacion_str = request.args.get('ecuacion')
        a = request.args.get('a', type=float)
        b = request.args.get('b', type=float)
        n = request.args.get('n', type=int)

        # Validaciones básicas
        if None in (ecuacion_str, a, b, n):
            return jsonify({"error": "Parámetros faltantes: necesita 'ecuacion', 'a', 'b' y 'n'"}), 400

        if a >= b:
            return jsonify({"error": "El valor de 'a' debe ser menor que 'b'"}), 400

        if n <= 0 or n % 2 != 0:
            return jsonify({"error": "El número de subintervalos 'n' debe ser un entero positivo y par"}), 400

        # Parsear ecuación
        x = symbols('x')
        try:
            ecuacion = parse_expr(ecuacion_str, transformations=transformations)
        except Exception as e:
            return jsonify({"error": f"Error en la ecuación: {str(e)}"}), 400

        # Calcular la integral real (simbólica)
        try:
            integral_real = float(N(integrate(ecuacion, (x, a, b))))
        except Exception as e:
            return jsonify({"error": f"No se pudo calcular la integral exacta: {str(e)}"}), 400

        # Método de Simpson y datos para graficar
        h = (b - a) / n
        suma = 0
        xi_list = []
        fxi_list = []
        try:
            for i in range(n + 1):
                xi = a + i * h
                fxi = N(ecuacion.subs(x, xi))
                xi_list.append(float(xi))
                fxi_list.append(float(fxi))
                if i == 0 or i == n:
                    suma += fxi
                elif i % 2 == 0:
                    suma += 2 * fxi
                else:
                    suma += 4 * fxi
        except Exception as e:
            return jsonify({"error": f"Error al evaluar la función: {str(e)}"}), 400

        resultado = float((h / 3) * suma)
        error = abs(integral_real - resultado)

        return jsonify({
            "integral_simpson": resultado,
            "integral_real": integral_real,
            "error_absoluto": error,
            "h": float(h),
            "n": n,
            "xi": xi_list,
            "fxi": fxi_list
        })

    except Exception as e:
        return jsonify({"error": f"Error inesperado: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5008, debug=True)