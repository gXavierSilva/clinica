from flask import Flask, jsonify, request
import psycopg2
from psycopg2 import sql, errors
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

def get_db_connection():
    conn = psycopg2.connect(
        host=app.config['DB_HOST'],
        database=app.config['DB_NAME'],
        user=app.config['DB_USER'],
        password=app.config['DB_PASSWORD'],
        port=app.config['DB_PORT']
    )
    return conn

def create_table():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Verifica se a tabela já existe
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'items'
            );
        """)
        table_exists = cur.fetchone()[0]
        
        if not table_exists:
            # Cria a tabela se não existir
            cur.execute("""
                CREATE TABLE items (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            print("Tabela 'items' criada com sucesso!")
        else:
            print("Tabela 'items' já existe.")
            
    except errors.DuplicateTable:
        conn.rollback()
        print("Tabela 'items' já existe.")
    except Exception as e:
        print(f"Erro ao criar tabela: {e}")
        conn.rollback()
    finally:
        if conn:
            cur.close()
            conn.close()

# Chama a função para criar a tabela ao iniciar a aplicação
create_table()

@app.route('/')
def hello():
    return jsonify({"message": "Bem-vindo à API PostgreSQL", 
                   "status": "Tabela 'items' verificada/criada automaticamente"})

# Rota para criar um novo item
@app.route('/items', methods=['POST'])
def create_item():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Nome do item é obrigatório"}), 400
        
    name = data.get('name')
    description = data.get('description', '')
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO items (name, description) VALUES (%s, %s) RETURNING id, name, description, created_at",
            (name, description)
        )
        new_item = cur.fetchone()
        conn.commit()
        
        return jsonify({
            "id": new_item[0],
            "name": new_item[1],
            "description": new_item[2],
            "created_at": new_item[3].isoformat()
        }), 201
        
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            cur.close()
            conn.close()

# Rota para listar todos os itens
@app.route('/items', methods=['GET'])
def get_items():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, description, created_at FROM items ORDER BY created_at DESC")
        items = cur.fetchall()
        
        items_list = []
        for item in items:
            items_list.append({
                "id": item[0],
                "name": item[1],
                "description": item[2],
                "created_at": item[3].isoformat()
            })
        
        return jsonify(items_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            cur.close()
            conn.close()

# Rota para buscar um item específico
@app.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, description, created_at 
            FROM items 
            WHERE id = %s
        """, (item_id,))
        item = cur.fetchone()
        
        if item is None:
            return jsonify({"error": "Item não encontrado"}), 404
        
        return jsonify({
            "id": item[0],
            "name": item[1],
            "description": item[2],
            "created_at": item[3].isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == '__main__':
    app.run(debug=True)