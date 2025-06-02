from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np

app = Flask(__name__)
CORS(app)

@app.route('/euler', methods=['GET'])
def euler():
    try:
        # Recibe: f (str), x0 (float), y0 (float), xf (float), n (int)
        f_str = request.args.get('f')
        x0 = float(request.args.get('x0', 0))
        y0 = float(request.args.get('y0', 0))
        xf = float(request.args.get('xf', 1))
        n = int(request.args.get('n', 10))
        if f_str is None or f_str.strip() == "":
            return jsonify({"error": "Debes enviar la función f como parámetro de la forma f='x+y'."}), 400
        if n < 1:
            return jsonify({"error": "El número de pasos n debe ser mayor que 0."}), 400

        # Define la función usando eval de forma segura (sólo x, y, np)
        def f(x, y):
            return eval(f_str, {"x": x, "y": y, "np": np, "__builtins__": {}})

        h = (xf - x0) / n
        xs = [x0]
        ys = [y0]
        fs = []
        for i in range(n):
            xn = xs[-1]
            yn = ys[-1]
            fn = f(xn, yn)
            fs.append(fn)
            yn1 = yn + h * fn
            xn1 = xn + h
            xs.append(xn1)
            ys.append(yn1)
        # Calcula f para el último punto
        fs.append(f(xs[-1], ys[-1]))

        # Calcular error si el usuario proporciona la solución exacta
        y_real_func_str = request.args.get("y_real", None)
        errores = []
        y_real_vals = []
        if y_real_func_str:
            try:
                def y_real(x):
                    return eval(y_real_func_str, {"x": x, "np": np, "__builtins__": {}})
                y_real_vals = [y_real(x) for x in xs]
                errores = [abs(ys[i] - y_real_vals[i]) for i in range(len(xs))]
            except Exception as e:
                y_real_vals = []
                errores = []
        else:
            y_real_vals = []
            errores = []

        tabla = [{"i": i, "x": xs[i], "y": ys[i], "f": fs[i], "error": errores[i] if errores else None, "y_real": y_real_vals[i] if y_real_vals else None} for i in range(n+1)]

        return jsonify({
            "tabla": tabla,
            "h": h,
            "x": xs,
            "y": ys,
            "f_vals": fs,
            "n": n,
            "f": f_str,
            "x0": x0,
            "y0": y0,
            "xf": xf,
            "errores": errores,
            "y_real": y_real_vals
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5010, debug=True)