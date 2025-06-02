from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np

app = Flask(__name__)
CORS(app)

def resolver_placa(n, top, bottom, left, right, tol=1e-4, max_iter=10000):
    # Inicializar la matriz de temperaturas
    T = np.zeros((n+2, n+2))
    T[0, :] = top
    T[-1, :] = bottom
    T[:, 0] = left
    T[:, -1] = right

    # Generar ecuaciones de diferencias finitas
    ecuaciones = []
    for i in range(1, n+1):
        for j in range(1, n+1):
            ecuaciones.append(f"T[{i},{j}] = 0.25 * (T[{i+1},{j}] + T[{i-1},{j}] + T[{i},{j+1}] + T[{i},{j-1}])")

    # Resolver el sistema de ecuaciones utilizando diferencias finitas
    for _ in range(max_iter):
        T_old = T.copy()
        for i in range(1, n+1):
            for j in range(1, n+1):
                T[i, j] = 0.25 * (T[i+1, j] + T[i-1, j] + T[i, j+1] + T[i, j-1])
        if np.max(np.abs(T - T_old)) < tol:
            break
    return T, ecuaciones

@app.route('/edpe', methods=['GET'])
def edpe():
    try:
        n = int(request.args.get('n', 3))
        top = float(request.args.get('top', 100))
        bottom = float(request.args.get('bottom', 100))
        left = float(request.args.get('left', 0))
        right = float(request.args.get('right', 0))
        tol = float(request.args.get('tol', 1e-4))
        max_iter = int(request.args.get('max_iter', 10000))

        T, ecuaciones = resolver_placa(n, top, bottom, left, right, tol, max_iter)

        # Solo la matriz interna (sin los bordes)
        matriz_resultado = T[1:-1, 1:-1].tolist()

        return jsonify({
            "matriz": matriz_resultado,
            "ecuaciones": ecuaciones,
            "n": n,
            "top": top,
            "bottom": bottom,
            "left": left,
            "right": right,
            "tol": tol,
            "max_iter": max_iter
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5009, debug=True)