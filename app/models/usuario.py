from dataclasses import dataclass
from flask_login import UserMixin


@dataclass
class Usuario(UserMixin):
    id: int
    nome: str
    cpf: str
    role: str
    unidade_id: int | None
    unidade_nome: str | None
    ativo: bool

    @property
    def is_active(self) -> bool:  # Flask-Login já usa esta propriedade
        return bool(self.ativo)

    @staticmethod
    def from_row(row: dict) -> "Usuario":
        return Usuario(
            id=row["id"],
            nome=row["nome"],
            cpf=row["cpf"],
            role=row["role"],
            unidade_id=row.get("unidade_id"),
            unidade_nome=row.get("unidade_nome"),
            ativo=row.get("ativo", 1) == 1,
        )

    def get_id(self) -> str:
        return str(self.id)