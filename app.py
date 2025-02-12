from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow


app = Flask(__name__)

# DB connection string
# <protocol>://<user>:<pass>@<host>:<port>/<db_name>
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://orm_dev:123456@localhost:5432/orm_db'

db = SQLAlchemy(app)
ma = Marshmallow(app)

# Model
# This just declares and configures the model in memory - the physical DB is unaffected.
class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float(precision=2), nullable=False)
    stock = db.Column(db.Integer, db.CheckConstraint('stock >= 0'), default = 0)    


# Schema
class ProductSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'description', 'price', "stock")



@app.route('/')
def home():
    return 'Hello!'

# R - Read (all
@app.route('/products')
def get_all_products():
    # Generate a statement
    # SELECT * FROM products;
    stmt = db.select(Product)
    # Execute the statement
    products = db.session.scalars(stmt)
    return ProductSchema(many=True).dump(products)

# R - Read (one
@app.route('/products/<int:product_id>')
def get_one_product(product_id):
    # check the db for a product with an id that matches
    # get product with given id
    # select * from products where id = product.id
    stmt = db.select(Product).filter_by(id=product_id)
    product = db.session.scalar(stmt)
    if product:
        return ProductSchema().dump(product)
    else:
        return {"error": f"product with id {product_id} not found"}, 404

# C - Create (one)

@app.route('/products', methods=['POST'])
def create_product():
    # parse the incoming json body
    data = ProductSchema(exclude=['id']).load(request.json)
    new_product = Product(
        name = data['name'],
        description = data.get('description', ''), 
        price = data['price'],
        stock = data.get('stock')
    )
    db.session.add(new_product)
    db.session.commit()
    return ProductSchema().dump(new_product), 201
    # Add to db session
    # commit to db
    #return the new project

# Delete Product
# DELETE /products/<int:product_id>
# 1. Select the product with the given product_id
# 2. Execute the statement (scalar)
# 3. Delete the product if exists, otherwise return error
# 4. If deletion success, return status code with no content
@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_one_product(product_id):
    # check the db for a product with an id that matches
    # get product with given id
    # select * from products where id = product.id
    stmt = db.select(Product).filter_by(id=product_id)
    product = db.session.scalar(stmt)
    if product:
        db.session.delete(product)
        db.session.commit()
        return {}, 204 
    else:
        return {"error": f"product with id {product_id} not found"}, 404


# U- update a product
# 1. Create statement to select the product with the given product_id
# 2. Execute the statement (scalar)
# 3. If the product exsits, update the field and commit, then reutn the update 

@app.route('/products/<int:product_id>', methods=['PUT'])
def update_one_product(product_id):
    data = ProductSchema(exclude=['id']).load(request.json)
    stmt = db.select(Product).filter_by(id=product_id)
    product = db.session.scalar(stmt)
    if product:
        product.name = data['name'],
        product.description = data.get('description', ''), 
        product.price = data['price'],
        product.stock = data.get('stock')

        db.session.commit()
    
        return ProductSchema().dump(product),200
    else:
        return {"error": f"product with id {product_id} not found"}, 404


@app.cli.command('init_db')
def init_db():
    db.drop_all()
    db.create_all()
    print('Created tables')

@app.cli.command('seed_db')
def seed_db():
    products = [
        Product(
            name='Product 1',
            description='This is a new product',
            price=12.99,
            stock=15
        ),
        Product(
            name='Product 2',
            description='Second product',
            price=49.95,
            stock=10
        )
    ]

    # db.delete(Product)
    db.session.add_all(products)

    db.session.commit()

    print('DB Seeded')