from flask import Flask, jsonify

app = Flask(__name__)

# Lista de microservicios registrados
methods = [
    {"id": 1, "name": "Biseccion", "description": "Encuentra raices por intervalos", "url": "http://localhost:5001/bisection"},
    {"id": 2, "name": "Newton-Raphson", "description": "Metodo iterativo para hallar raices", "url": "http://localhost:5002/newton_raphson"},
    {"id": 3, "name": "Newton-Raphson", "description": "Método iterativo para hallar raíces", "url": "http://localhost:5003/newton_raphson"},
    {"id": 4, "name": "Secante", "description": "Método numérico para encontrar raíces sin derivadas", "url": "http://localhost:5004/secante"}
]

@app.route("/methods", methods=['GET'])
def get_methods():
    return jsonify(methods)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
