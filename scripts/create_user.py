import argparse

from app import create_app
from app.utils.security import hash_password
from app.repositories import usuarios as usuarios_repo

app = create_app()


def main():
    parser = argparse.ArgumentParser(description="Criar usuário no sistema.")
    parser.add_argument("--nome", required=True)
    parser.add_argument("--cpf", required=True)
    parser.add_argument("--senha", required=True)
    parser.add_argument(
        "--role",
        required=True,
        choices=[
            "admin",
            "recepcao",
            "malote",
            "medico_regulador",
            "agendador_municipal",
            "agendador_estadual",
        ],
    )
    parser.add_argument("--unidade-id", type=int)
    args = parser.parse_args()

    with app.app_context():
        senha_hash = hash_password(args.senha)
        usuario_id = usuarios_repo.criar_usuario(
            nome=args.nome,
            cpf=args.cpf,
            senha_hash=senha_hash,
            role=args.role,
            unidade_id=args.unidade_id,
        )
        print(f"Usuário criado com ID {usuario_id}.")


if __name__ == "__main__":
    main()