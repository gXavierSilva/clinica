from flask import Flask, jsonify, request, render_template
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
                WHERE table_name = 'users'
            );
        """)
        table_exists = cur.fetchone()[0]
        
        if not table_exists:
            # Cria a tabela se não existir
            cur.execute("""
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password CHAR(60) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                );
            """)
            conn.commit()
            print("Tabela 'users' criada com sucesso!")
        else:
            print("Tabela 'users' já existe.")
            
    except errors.DuplicateTable:
        conn.rollback()
        print("Tabela 'users' já existe.")
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
                   "status": "Tabela 'users' verificada/criada automaticamente"})

# Rota para criar um novo usuário
@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data or 'name' not in data or 'email' not in data or 'password' not in data:
        return jsonify({"error": "As credenciais são obrigatórias."}), 400
        
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    # password = data.get('password', '')
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s) RETURNING id, name, email, password, created_at, is_active",
            (name, email, password)
        )
        new_item = cur.fetchone()
        conn.commit()
        
        return jsonify({
            "id": new_item[0],
            "name": new_item[1],
            "email": new_item[2],
            "password": new_item[3],
            "created_at": new_item[4].isoformat(),
            "is_active": new_item[5]
        }), 201
        
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            cur.close()
            conn.close()

# Rota para listar todos os usuários
@app.route('/users', methods=['GET'])
def get_users():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, email, password, created_at, is_active FROM users ORDER BY created_at DESC")
        users = cur.fetchall()
        
        users_list = []
        for user in users:
            users_list.append({
                "id": user[0],
                "name": user[1],
                "email": user[2],
                "password": user[3],
                "created_at": user[4].isoformat(),
                "is_active": user[5]
            })
        
        return jsonify(users_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            cur.close()
            conn.close()

# Rota para buscar um usuário específico
@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, email, password, created_at, is_active 
            FROM users 
            WHERE id = %s
        """, (user_id,))
        user = cur.fetchone()
        
        if user is None:
            return jsonify({"error": "Usuário não encontrado"}), 404
        
        return jsonify({
            "id": user[0],
            "name": user[1],
            "email": user[2],
            "password": user[3],
            "created_at": user[4].isoformat(),
            "is_active": user[5]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            cur.close()
            conn.close()

# Renderiza página de registro
@app.route('/register')
def register():
    return render_template('register.html')

# Renderiza página de dashboard
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# Renderiza página de login
@app.route('/login', methods=['GET'])
def login_page():
    return render_template('clinicsoft-login.html')

# Consulta o banco de dados buscando um usuário
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user:
        return jsonify({"success": True, "redirect": "/dashboard"})
    else:
        return jsonify({"success": False, "message": "Credenciais inválidas"}), 401

if __name__ == '__main__':
    app.run(debug=True)