from flask import Flask, jsonify

app = Flask(__name__)

# Lista de microservicios registrados
methods = [
    {"id": 1, "name": "Punto Fijo", "description": "Método iterativo basado en funciones de iteración", "url": "http://localhost:5001/punto_fijo"},
    {"id": 2, "name": "Bisección", "description": "Encuentra raíces por intervalos", "url": "http://localhost:5002/bisection"},
    {"id": 3, "name": "Newton-Raphson", "description": "Método iterativo para hallar raíces", "url": "http://localhost:5003/newton_raphson"},
    {"id": 4, "name": "Secante", "description": "Método numérico para encontrar raíces sin derivadas", "url": "http://localhost:5004/secante"},
    {"id": 4, "name": "jacobi", "description": "Método numérico iterativo para para resolver ecuaciones lineales", "url": "http://localhost:5005/jacobi"},
    {"id": 4, "name": "gauss-seidel", "description": "Método numérico iterativo para para resolver ecuaciones lineales con presicion albitraria", "url": "http://localhost:5006/gauss-seidel"}
]


@app.route("/methods", methods=['GET'])
def get_methods():
    return jsonify(methods)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
