"""
patch_models_estrelas.py - Adiciona 2 classes SQLModel ao models.py.

Classes adicionadas:
  - RefEstrelasNascimento  (12 linhas no banco)
  - RefHabilidadesEstrela  (1200 linhas, FK -> estrelas)

Segue o estilo sqlacodegen-generated ja presente no arquivo:
  - __tablename__ explicito
  - __table_args__ com todas as constraints
  - Field(sa_column=Column(...)) pra cada campo
  - NOT NULL primeiro, Optional depois
  - Relationship bidirecional no final
"""
from pathlib import Path
import sys

MODELS = Path("models.py")
SENTINELA = "# === ESTRELAS DO VEU (Modulo 5.1) ==="

NOVAS_CLASSES = '''


# === ESTRELAS DO VEU (Modulo 5.1) ===

class RefEstrelasNascimento(SQLModel, table=True):
    __tablename__ = 'ref_estrelas_nascimento'
    __table_args__ = (
        CheckConstraint('pct_primeira_cat >= 1 AND pct_primeira_cat <= 99', name='ref_estrelas_nascimento_pct_primeira_cat_check'),
        CheckConstraint('pct_segunda_cat >= 1 AND pct_segunda_cat <= 99', name='ref_estrelas_nascimento_pct_segunda_cat_check'),
        CheckConstraint('pct_terceira_cat >= 1 AND pct_terceira_cat <= 99', name='ref_estrelas_nascimento_pct_terceira_cat_check'),
        PrimaryKeyConstraint('id', name='ref_estrelas_nascimento_pkey'),
        UniqueConstraint('nome', name='ref_estrelas_nascimento_nome_key')
    )

    id: int = Field(sa_column=Column('id', Integer, primary_key=True))
    nome: str = Field(sa_column=Column('nome', Text, nullable=False))
    epiteto: str = Field(sa_column=Column('epiteto', Text, nullable=False))
    lema: str = Field(sa_column=Column('lema', Text, nullable=False))
    tema_central: str = Field(sa_column=Column('tema_central', Text, nullable=False))
    atributos_primarios: str = Field(sa_column=Column('atributos_primarios', Text, nullable=False))
    pct_terceira_cat: int = Field(sa_column=Column('pct_terceira_cat', Integer, nullable=False))
    pct_segunda_cat: int = Field(sa_column=Column('pct_segunda_cat', Integer, nullable=False))
    pct_primeira_cat: int = Field(sa_column=Column('pct_primeira_cat', Integer, nullable=False))
    habilidade_100_nome: str = Field(sa_column=Column('habilidade_100_nome', Text, nullable=False))
    habilidade_100_descricao: str = Field(sa_column=Column('habilidade_100_descricao', Text, nullable=False))

    habilidades: list['RefHabilidadesEstrela'] = Relationship(back_populates='estrela')


class RefHabilidadesEstrela(SQLModel, table=True):
    __tablename__ = 'ref_habilidades_estrela'
    __table_args__ = (
        CheckConstraint('categoria = ANY (ARRAY[1, 2, 3])', name='ref_habilidades_estrela_categoria_check'),
        CheckConstraint('numero_d100 >= 1 AND numero_d100 <= 100', name='ref_habilidades_estrela_numero_d100_check'),
        ForeignKeyConstraint(['estrela_id'], ['ref_estrelas_nascimento.id'], name='ref_habilidades_estrela_estrela_id_fkey'),
        PrimaryKeyConstraint('id', name='ref_habilidades_estrela_pkey'),
        UniqueConstraint('estrela_id', 'numero_d100', name='ref_habilidades_estrela_estrela_id_numero_d100_key'),
        Index('idx_habilidades_categoria', 'estrela_id', 'categoria'),
        Index('idx_habilidades_estrela_lookup', 'estrela_id', 'numero_d100')
    )

    id: int = Field(sa_column=Column('id', Integer, primary_key=True))
    estrela_id: int = Field(sa_column=Column('estrela_id', Integer, nullable=False))
    numero_d100: int = Field(sa_column=Column('numero_d100', Integer, nullable=False))
    nome: str = Field(sa_column=Column('nome', Text, nullable=False))
    descricao_completa: str = Field(sa_column=Column('descricao_completa', Text, nullable=False))
    categoria: int = Field(sa_column=Column('categoria', Integer, nullable=False))
    tem_preco: bool = Field(sa_column=Column('tem_preco', Boolean, nullable=False, server_default=text('false')))
    evolucao_grau2_descricao: Optional[str] = Field(default=None, sa_column=Column('evolucao_grau2_descricao', Text))
    evolucao_grau3_descricao: Optional[str] = Field(default=None, sa_column=Column('evolucao_grau3_descricao', Text))
    condicao_evolucao: Optional[str] = Field(default=None, sa_column=Column('condicao_evolucao', Text))
    descricao_preco: Optional[str] = Field(default=None, sa_column=Column('descricao_preco', Text))

    estrela: 'RefEstrelasNascimento' = Relationship(back_populates='habilidades')
'''


def main() -> int:
    if not MODELS.exists():
        print(f"[ERRO] {MODELS} nao encontrado. Rode na raiz do projeto.")
        return 1

    conteudo = MODELS.read_text(encoding="utf-8")
    tam_antes = len(conteudo)

    if SENTINELA in conteudo:
        print("=" * 72)
        print("  [IDEMPOTENTE] Classes ja existem em models.py. Nada a fazer.")
        print(f"  Tamanho atual: {tam_antes} bytes")
        print("=" * 72)
        return 0

    # Remove whitespace trailing, adiciona as classes, garante newline final
    novo_conteudo = conteudo.rstrip() + NOVAS_CLASSES + "\n"
    MODELS.write_text(novo_conteudo, encoding="utf-8")

    tam_depois = len(novo_conteudo)
    print("=" * 72)
    print("  [OK] models.py patched com sucesso.")
    print(f"  Tamanho antes:  {tam_antes:>6} bytes")
    print(f"  Tamanho depois: {tam_depois:>6} bytes ({tam_depois - tam_antes:+d})")
    print(f"  Classes adicionadas: RefEstrelasNascimento, RefHabilidadesEstrela")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())