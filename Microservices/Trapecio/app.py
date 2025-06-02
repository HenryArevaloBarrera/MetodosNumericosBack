from flask import Flask, request, jsonify
from sympy import symbols, N, integrate
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Transformaciones para permitir multiplicación implícita
transformations = (standard_transformations + (implicit_multiplication_application,))

@app.route('/trapecio', methods=['GET'])
def metodo_trapecio():
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

        if n <= 0:
            return jsonify({"error": "El número de subdivisiones 'n' debe ser mayor que 0"}), 400

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

        # Calcular la integral por el método del trapecio y recolectar datos para graficar
        try:
            h = (b - a) / n
            suma = 0.0
            xi_list = []
            fxi_list = []

            for i in range(n + 1):
                xi = a + i * h
                fxi = N(ecuacion.subs(x, xi))
                xi_list.append(float(xi))
                fxi_list.append(float(fxi))

                # Ponderar los extremos
                if i == 0 or i == n:
                    suma += fxi
                else:
                    suma += 2 * fxi

            integral_trapecio = float((h / 2) * suma)
            error = abs(integral_real - integral_trapecio)

        except Exception as e:
            return jsonify({"error": f"Error al calcular la integral: {str(e)}"}), 400

        return jsonify({
            "integral_trapecio": integral_trapecio,
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
    app.run(host='0.0.0.0', port=5007, debug=True)