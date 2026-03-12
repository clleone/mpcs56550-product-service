from flask import Flask, request, jsonify
from flask_cors import CORS
import db
from prometheus_flask_exporter import PrometheusMetrics

### Product Catalog ###

app = Flask(__name__)
CORS(app)

metrics = PrometheusMetrics(app, default_metrics_path="/prometheus-metrics")


@app.route("/health")
def health():
    try:
        conn = db.get_db_connection()
        conn.close()
        return {"status": "healthy"}, 200
    except Exception as e:
        return {"error": str(e)}, 503


@app.route("/products", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        query = "SELECT * FROM products WHERE quantity > 0;"
        try:
            result = db.read_from_db(query)
            keys = ["id", "item", "quantity", "price"]
            products = [dict(zip(keys, row)) for row in result]
            for p in products:
                p["price"] = float(p["price"])
            print(type(products[0]["price"]))
            return jsonify(products), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        item = request.json["item"]
        quantity = request.json["quantity"]
        price = float(request.json["price"])
        print("item:", type(item), "quantity", type(quantity), "price", type(price))

        query = "INSERT INTO products (item, quantity, price) VALUES (%s, %s, %s)"
        params = (item, quantity, price)
        try:
            db.write_to_db(query, params)
            return jsonify({"message": f"{item} has been added to products."}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500


@app.route("/products/<int:id>", methods=["PUT"])
def update_quantities(id):
    is_additional = bool(request.json["additional"])
    increment = int(request.json["increment"])

    # calculate new quantity
    query = "SELECT item, quantity FROM products WHERE id = %s"
    params = (id,)
    try:
        results = db.read_from_db(query, params)[0]
        item = results[0]
        current_quantity = int(results[2])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # increasing quantity
    if is_additional:
        new_quantity = current_quantity + increment
    # decreasing quantity
    else:
        new_quantity = current_quantity - increment
        if new_quantity < 0:
            return jsonify({"error": "Stock quantity must be at least zero."}), 500

    # schema: id, item name, quantity, price
    query = "UPDATE products SET quantity = %s WHERE item = %s"
    params = (new_quantity, item)
    try:
        db.write_to_db(query, params)
        return jsonify({"message": f"{item} quantity updated successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
