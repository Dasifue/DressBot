from sqlalchemy import Engine, text

class DBManager():

    def __init__(self, engine: Engine):
        self.engine = engine


    def _create_user(self):
        with self.engine.connect() as connection:
            user = """
                CREATE TABLE IF NOT EXISTS user (
                                id BIGINT PRIMARY KEY NOT NULL,
                                username VARCHAR(100),
                                email VARCHAR(100) UNIQUE,
                                first_name VARCHAR(100),
                                last_name VARCHAR(100),
                                phone_number VARCHAR(100),
                                registered DATETIME DEFAULT now()
                ); 
            """
            connection.execute(text(user))

    def _create_category(self):
        with self.engine.connect() as connection:
            category = """
            CREATE TABLE IF NOT EXISTS category  ( 
                            id INTEGER PRIMARY KEY auto_increment,
                            name VARCHAR(100) NOT NULL, 
                            description TEXT 
            );
            """
            connection.execute(text(category))

    
    def _create_dress(self):
        with self.engine.connect() as connection:
            dress = """
                CREATE TABLE IF NOT EXISTS dress ( 
                                id INTEGER PRIMARY KEY auto_increment, 
                                category_id INTEGER NOT NULL, 
                                name VARCHAR(100) NOT NULL, 
                                description TEXT, 
                                price DECIMAL(6,2) UNSIGNED DEFAULT 5, 
                                discount TINYINT UNSIGNED default 0,
                                image TEXT,
                                FOREIGN KEY (category_id) REFERENCES category(id)
                );
            """
            connection.execute(text(dress))


    def _create_cart(self):
        with self.engine.connect() as connection:
            cart = """
                CREATE TABLE IF NOT EXISTS cart (
                                id INTEGER PRIMARY KEY auto_increment,
                                user_id BIGINT NOT NULL,
                                is_active BOOL DEFAULT true,
                                created DATETIME DEFAULT now(),
                                FOREIGN KEY (user_id) REFERENCES user(id)
                );
            """

            connection.execute(text(cart))

    
    def _create_cart_product(self):
        with self.engine.connect() as connection:
            cart_product = """
                CREATE TABLE IF NOT EXISTS cart_product (
                                id INTEGER PRIMARY KEY auto_increment,
                                dress_id INTEGER NOT NULL,
                                cart_id INTEGER NOT NULL,
                                FOREIGN KEY (dress_id) REFERENCES dress(id),
                                FOREIGN KEY (cart_id) REFERENCES cart(id)
                );
            """
            connection.execute(text(cart_product))



    def create_tables(self):
        self._create_user()
        self._create_category()
        self._create_dress()
        self._create_cart()
        self._create_cart_product()



    def select_categories(self, *params):
        with self.engine.connect() as connection:

            if not params:
                request = f"SELECT * FROM category;"
            else:
                params = ", ".join(params)
                request = f"SELECT {params} FROM category;"

            result = connection.execute(text(request))
        return result
    

    def select_category_dress(self, category_id, *params):
        with self.engine.connect() as connection:

            if not params:
                request = f"SELECT * FROM dress WHERE category_id={category_id};"
            else:
                params = ", ".join(params)
                request = f"SELECT {params} FROM dress WHERE category_id={category_id};" 
            
            result = connection.execute(text(request))
        return result
        

    def select_dress(self, dress_id, *params):
        with self.engine.connect() as connection:
            if not params:
                request = f"SELECT * FROM dress WHERE id={dress_id};"
            else:
                params = ", ".join(params)
                request = f"SELECT {params} FROM dress WHERE id={dress_id};"
            result = connection.execute(text(request))
        return result
    

    def get_user_cart(self, user_id):
        with self.engine.connect() as connection:
            request = f"SELECT * FROM cart WHERE user_id={user_id} and is_active=true;"
            result = connection.execute(text(request)).fetchone()

            if result is None:
                request = f"INSERT INTO cart (user_id) VALUES ({user_id});"
                connection.execute(text(request))
                connection.commit()
                return self.get_user_cart(user_id=user_id)
            else:
                return result


    def insert_user(self, data: dict):
        with self.engine.connect() as connection:
            keys_ = ", ".join(data.keys())
            values_ = ", ".join(data.values())

            request = f"INSERT INTO user ({keys_}) VALUES ({values_})"
            connection.execute(text(request))
            connection.commit()

    
    def get_user(self, user_id, *params):
        with self.engine.connect() as connection:
            if not params:
                request = f"SELECT * FROM user WHERE id = {user_id};"
            else:
                params = ", ".join(params)
                request = f"SELECT {params} FROM user WHERE id = {user_id};"

            result = connection.execute(text(request)).fetchone()
        return result
            
            

    def insert_cart_product(self, cart_id, dress_id):
        with self.engine.connect() as connection:
            request = f"INSERT INTO cart_product (cart_id, dress_id) VALUES ({cart_id}, {dress_id});"
            connection.execute(text(request))
            connection.commit()


    def select_cart_products(self, cart_id, *params):
        with self.engine.connect() as connection:
            if not params:
                request = f"SELECT * FROM cart_product WHERE cart_id={cart_id};"
            else:
                params = ", ".join(params)
                request = f"SELECT {params} FROM cart_product WHERE cart_id={cart_id};"
                
            result = connection.execute(text(request))
        return result


    def delete_cart_product(self, cart_product_id):
        with self.engine.connect() as connection:
            request = f"DELETE FROM cart_product WHERE id={cart_product_id}"
            connection.execute(text(request))
            connection.commit()

    def deactivate_cart(self, cart_id):
        with self.engine.connect() as connection:
            request = f"UPDATE cart SET is_active=false WHERE id={cart_id};"
            connection.execute(text(request))
            connection.commit()
            