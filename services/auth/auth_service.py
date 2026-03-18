from fastapi import APIRouter, Depends, HTTPException
from passlib.context import CryptContext

from api.database import get_db
from api.dependencies import create_access_token, get_current_user
from api.models import UserLogin, UserCreate, UserResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentification"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _user_to_response(row: dict) -> dict:
    return {
        "id": str(row["id_utilisateur"]),
        "email": row["email"],
        "firstName": row.get("first_name") or "",
        "lastName": row.get("last_name") or "",
        "role": "admin" if row["is_admin"] else "user",
    }


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM utilisateur WHERE email = %s", (data.email,))
        user = cur.fetchone()

    if not user or not pwd_context.verify(data.password, user["password_hash"]):
        raise HTTPException(401, "Email ou mot de passe incorrect")

    token = create_access_token({"sub": str(user["id_utilisateur"]), "email": user["email"]})
    return {"user": _user_to_response(user), "token": token}


@router.post("/register", response_model=TokenResponse)
def register(data: UserCreate):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM utilisateur WHERE email = %s", (data.email,))
        if cur.fetchone():
            raise HTTPException(400, "Email déjà utilisé")

        hashed = pwd_context.hash(data.password)
        cur.execute(
            """INSERT INTO utilisateur (email, password_hash, first_name, last_name)
               VALUES (%s, %s, %s, %s) RETURNING *""",
            (data.email, hashed, data.firstName, data.lastName),
        )
        user = cur.fetchone()

    token = create_access_token({"sub": str(user["id_utilisateur"]), "email": user["email"]})
    return {"user": _user_to_response(user), "token": token}


@router.get("/verify", response_model=UserResponse)
def verify(current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM utilisateur WHERE id_utilisateur = %s", (current_user["sub"],))
        user = cur.fetchone()

    if not user:
        raise HTTPException(404, "Utilisateur introuvable")
    return _user_to_response(user)
