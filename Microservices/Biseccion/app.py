from flask import Flask, request, jsonify
from sympy import symbols, N
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
from flask_cors import CORS
import numpy as np

app = Flask(__name__)
CORS(app)

# Transformaciones para permitir multiplicación implícita
transformations = (standard_transformations + (implicit_multiplication_application,))

@app.route('/biseccion', methods=['GET'])
def metodo_biseccion():
    try:
        # Obtener parámetros
        ecuacion_str = request.args.get('ecuacion')
        xo = request.args.get('xo', type=float)
        xu = request.args.get('xu', type=float)
        tol_error = request.args.get('tol_error', type=float)

        # Validaciones básicas
        if None in (ecuacion_str, xo, xu, tol_error):
            return jsonify({"error": "Parámetros faltantes: necesita 'ecuacion', 'xo', 'xu' y 'tol_error'"}), 400

        if xo >= xu:
            return jsonify({"error": "El valor de 'xo' debe ser menor que 'xu'"}), 400

        if tol_error <= 0 or tol_error >= 1:
            return jsonify({"error": "El error debe ser 0 < tol_error < 1"}), 400

        # Parsear ecuación
        x = symbols('x')
        try:
            ecuacion = parse_expr(ecuacion_str, transformations=transformations)
        except Exception as e:
            return jsonify({"error": f"Error en la ecuación: {str(e)}"}), 400

        # Evaluar en los extremos
        try:
            fxo = N(ecuacion.subs(x, xo))  # Convertir a número flotante
            fxu = N(ecuacion.subs(x, xu))
        except Exception as e:
            return jsonify({"error": f"Error al evaluar: {str(e)}"}), 400

        if fxo * fxu >= 0:
            return jsonify({
                "error": "No hay cambio de signo en el intervalo [xo, xu]",
                "f(xo)": float(fxo),
                "f(xu)": float(fxu)
            }), 400

        # Algoritmo de bisección corregido
        nIteracion = 0
        error = 1.0
        xm_previo = xo  # Inicializar con xo para primera iteración
        tabla = []

        while error >= tol_error and nIteracion < 100:
            nIteracion += 1
            xm = (xo + xu) / 2
            fxm = N(ecuacion.subs(x, xm))

            # Calcular error relativo porcentual
            if nIteracion > 1:  # No calcular error en primera iteración
                error = abs((xm - xm_previo) / xm) if xm != 0 else 0

            # Guardar valores antes de actualizar
            xo_prev, xu_prev = xo, xu

            # Actualizar intervalo correctamente
            if fxo * fxm < 0:
                xu = xm
                fxu = fxm
            else:
                xo = xm
                fxo = fxm

            # Guardar iteración
            tabla.append({
                "nIteracion": nIteracion,
                "xo": float(xo_prev),
                "xu": float(xu_prev),
                "xm": float(xm),
                "fxm": float(fxm),
                "error": float(error) if nIteracion > 1 else 1.0  # Primer error es 100%
            })

            # Actualizar xm_previo para siguiente iteración
            xm_previo = xm

            # Condición de parada adicional por convergencia
            if fxm == 0:
                break

        # --- DATOS PARA EL GRÁFICO ---
        grafico_x = np.linspace(float(request.args.get('xo')), float(request.args.get('xu')), 100)
        grafico_y = []
        for val in grafico_x:
            try:
                yval = float(N(ecuacion.subs(x, val)))
            except:
                yval = None
            grafico_y.append(yval)

        return jsonify({
            "tabla": tabla,
            "grafico_x": grafico_x.tolist(),
            "grafico_y": grafico_y
        })

    except Exception as e:
        return jsonify({"error": f"Error inesperado: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)