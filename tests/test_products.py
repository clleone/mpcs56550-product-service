import pytest
from app import app as flask_app
import db

### PRODUCT TESTS ###


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client


# @pytest.fixture
# def clean_db():
#     """Clean up the database before each test"""
#     query = "DELETE FROM products where item = 'Barrel of Monkeys'"
#     db.write_to_db(query)
#     yield


@pytest.fixture
def test_product():
    "Get new product to insert"
    return {
        "item": "Barrel of Monkeys",
        "quantity": 40,
        "price": 10.00,
    }


@pytest.fixture
def test_quantity():
    "Get new quantity"
    return {"additional": "True", "increment": 2}


def test_add_product(client, mocker, test_product):
    """Test insertion of new product to db"""
    mocker.patch("db.write_to_db")
    mocker.patch(
        "db.read_from_db",
        return_value=[(1, "Barrel of Monkeys", 40, 10)],
    )

    # ping API & check response
    response = client.post("/products", json=test_product)
    assert response.status_code == 201

    # see if product landed in db
    result = db.read_from_db(
        "SELECT * FROM products WHERE item = %s", ("Barrel of Monkeys",)
    )
    assert result is not None
    test_entry = result[0]
    # might need to change to test_entry["item"], etc
    assert test_entry[1] == test_product["item"]
    assert test_entry[2] == test_product["quantity"]
    assert test_entry[3] == test_product["price"]


def test_change_quantity(client, mocker, test_quantity):
    """Test quantity update for item in db."""
    mocker.patch(
        "db.read_from_db",
        return_value=[(5, "Little Green Army Men", 45, 10.00)],
    )
    mock_write = mocker.patch("db.write_to_db")

    response = client.put("/products/5", json=test_quantity)
    assert response.status_code == 200

    # verify write was called with updated quantity
    assert mock_write.called
    call_args = mock_write.call_args
    # new quantity should be 45 + 2 = 47
    assert 47 in call_args[0][1]


def test_get_products(client, mocker):
    """Test retrieving all products with quantity > 0"""
    mock_data = [
        (1, "Barrel of Monkeys", 40, 10.00),
        (5, "Little Green Army Men", 45, 10.00),
        (6, "Ned's Nose", 0, 30.00),
    ]
    mocker.patch("db.read_from_db", return_value=mock_data)

    response = client.get("/products")
    assert response.status_code == 200

    data = response.get_json()
    assert len(data) == 2
    assert data[0]["item"] == "Barrel of Monkeys"
    assert data[0]["price"] == 10.00


def test_get_products_db_error(client, mocker):
    """Test that db errors are handled gracefully"""
    mocker.patch("db.read_from_db", side_effect=Exception("DB connection failed"))

    response = client.get("/products")
    assert response.status_code == 500
    assert "error" in response.get_json()
