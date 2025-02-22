from flask import Flask, request, jsonify
from sympy import symbols, sympify
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

app = Flask(__name__)

# Transformaciones para permitir multiplicación implícita (por ejemplo, 2x en lugar de 2*x)
transformations = (standard_transformations + (implicit_multiplication_application,))

def punto_fijo(f, g, x0, tol=1e-6, max_iter=100):
    """
    Método de punto fijo para encontrar la raíz de una ecuación.

    Parámetros:
    f: función original f(x)
    g: función transformada g(x)
    x0: punto inicial
    tol: tolerancia para la convergencia
    max_iter: número máximo de iteraciones

    Retorna:
    Una tabla con las iteraciones, xi, g(xi), y f(xi)
    """
    tabla = []
    xi = x0
    for i in range(max_iter):
        gxi = g(xi)
        fxi = f(xi)
        tabla.append((i, xi, gxi, fxi))
        
        if abs(gxi - xi) < tol:
            break
        
        xi = gxi
    
    return tabla

def encontrar_x0(f, rango=10):
    """
    Encuentra un punto inicial x0 entero cercano a 0.

    Parámetros:
    f: función original f(x)
    rango: rango de búsqueda para x0

    Retorna:
    x0: punto inicial entero
    """
    for x0 in range(-rango, rango + 1):
        if abs(f(x0)) < abs(f(x0 + 1)):
            return x0
    return 0

@app.route('/punto_fijo', methods=['GET'])
def metodo_punto_fijo():
    # Obtener la ecuación original y la transformada desde la URL
    ecuacion_str = request.args.get('ecuacion')
    transformada_str = request.args.get('transformada')
    
    if not ecuacion_str or not transformada_str:
        return jsonify({"error": "Debes proporcionar tanto 'ecuacion' como 'transformada' en los parámetros de la URL"}), 400

    try:
        # Convertir las ecuaciones en expresiones simbólicas
        x = symbols('x')
        ecuacion = parse_expr(ecuacion_str, transformations=transformations)
        transformada = parse_expr(transformada_str, transformations=transformations)

        # Definir la función f(x) y g(x)
        def f(x_val):
            return ecuacion.subs(x, x_val).evalf()

        def g(x_val):
            return transformada.subs(x, x_val).evalf()

        # Encontrar x0
        x0 = encontrar_x0(f)
        
        # Aplicar el método de punto fijo
        tabla = punto_fijo(f, g, x0)

        # Convertir la tabla en un formato JSON
        resultados = []
        for fila in tabla:
            resultados.append({
                'iteracion': fila[0],
                'xi': float(fila[1]),
                'g(xi)': float(fila[2]),
                'f(xi)': float(fila[3])
            })

        return jsonify(resultados)

    except Exception as e:
        return jsonify({"error": f"Error al procesar las ecuaciones: {str(e)}"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)