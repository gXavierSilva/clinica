from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from models import Usuario, SessionLocal, Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"mensagem":"API está funcionando"}

# @app.post("/usuarios/")
# def criar_usuario(nome: str, email: str, db: Session = Depends(get_db)):
#     db_usuario = Usuario(nome=nome, email=email)
#     db.add(db_usuario)
#     db.commit()
#     db.refresh(db_usuario)
#     return db_usuario

# @app.get("/usuarios/")
# def listar_usuarios(db: Session = Depends(get_db)):
#     return db.query(Usuario).all()