"""
patch_models_vocacoes.py - Adiciona 3 classes SQLModel de vocacoes.

Classes:
  - RefVocacoes (126 linhas: 40 base + 86 fundidas)
  - RefCaminhos (88 linhas, FK -> vocacoes)
  - RefHabilidadesClasseNivel (320 linhas, FK -> vocacoes)
"""
from pathlib import Path
import sys

MODELS = Path("models.py")
SENTINELA = "# === VOCACOES (Modulo 6.1) ==="

NOVAS_CLASSES = '''


# === VOCACOES (Modulo 6.1) ===

class RefVocacoes(SQLModel, table=True):
    __tablename__ = 'ref_vocacoes'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='ref_vocacoes_pkey'),
        UniqueConstraint('nome', name='ref_vocacoes_nome_key')
    )

    id: int = Field(sa_column=Column('id', Integer, primary_key=True))
    nome: str = Field(sa_column=Column('nome', Text, nullable=False))
    nome_ptbr: str = Field(sa_column=Column('nome_ptbr', Text, nullable=False))
    pilar: str = Field(sa_column=Column('pilar', Text, nullable=False))
    tipo: str = Field(sa_column=Column('tipo', Text, nullable=False, server_default=text("'base'::text")))
    descricao: str = Field(sa_column=Column('descricao', Text, nullable=False))
    atributos_primarios: Optional[list[str]] = Field(default=None, sa_column=Column('atributos_primarios', ARRAY(Text())))
    vocacoes_origem: Optional[list[str]] = Field(default=None, sa_column=Column('vocacoes_origem', ARRAY(Text())))
    diferencial_mecanico: Optional[str] = Field(default=None, sa_column=Column('diferencial_mecanico', Text))
    disponivel_escolha: Optional[bool] = Field(default=None, sa_column=Column('disponivel_escolha', Boolean, server_default=text('true')))
    imagem_url: Optional[str] = Field(default=None, sa_column=Column('imagem_url', Text))
    criado_em: Optional[datetime.datetime] = Field(default=None, sa_column=Column('criado_em', DateTime, server_default=text('now()')))

    caminhos: list['RefCaminhos'] = Relationship(back_populates='vocacao')
    habilidades: list['RefHabilidadesClasseNivel'] = Relationship(back_populates='vocacao')


class RefCaminhos(SQLModel, table=True):
    __tablename__ = 'ref_caminhos'
    __table_args__ = (
        ForeignKeyConstraint(['vocacao_id'], ['ref_vocacoes.id'], name='ref_caminhos_vocacao_id_fkey'),
        PrimaryKeyConstraint('id', name='ref_caminhos_pkey'),
        UniqueConstraint('vocacao_id', 'nome', name='ref_caminhos_vocacao_id_nome_key')
    )

    id: int = Field(sa_column=Column('id', Integer, primary_key=True))
    vocacao_id: int = Field(sa_column=Column('vocacao_id', Integer, nullable=False))
    nome: str = Field(sa_column=Column('nome', Text, nullable=False))
    nome_ptbr: str = Field(sa_column=Column('nome_ptbr', Text, nullable=False))
    descricao: str = Field(sa_column=Column('descricao', Text, nullable=False))
    nivel_desbloqueio: Optional[int] = Field(default=None, sa_column=Column('nivel_desbloqueio', Integer, server_default=text('3')))
    habilidades_iniciais: Optional[dict] = Field(default=None, sa_column=Column('habilidades_iniciais', JSONB, server_default=text("'[]'::jsonb")))
    criado_em: Optional[datetime.datetime] = Field(default=None, sa_column=Column('criado_em', DateTime, server_default=text('now()')))

    vocacao: 'RefVocacoes' = Relationship(back_populates='caminhos')


class RefHabilidadesClasseNivel(SQLModel, table=True):
    __tablename__ = 'ref_habilidades_classe_nivel'
    __table_args__ = (
        CheckConstraint('nivel >= 1 AND nivel <= 20', name='ref_habilidades_classe_nivel_nivel_check'),
        ForeignKeyConstraint(['vocacao_id'], ['ref_vocacoes.id'], name='ref_habilidades_classe_nivel_vocacao_id_fkey'),
        PrimaryKeyConstraint('id', name='ref_habilidades_classe_nivel_pkey'),
        UniqueConstraint('vocacao_id', 'nivel', 'nome', name='ref_habilidades_classe_nivel_vocacao_id_nivel_nome_key')
    )

    id: int = Field(sa_column=Column('id', Integer, primary_key=True))
    vocacao_id: int = Field(sa_column=Column('vocacao_id', Integer, nullable=False))
    nivel: int = Field(sa_column=Column('nivel', Integer, nullable=False))
    nome: str = Field(sa_column=Column('nome', Text, nullable=False))
    nome_ptbr: str = Field(sa_column=Column('nome_ptbr', Text, nullable=False))
    tipo: str = Field(sa_column=Column('tipo', Text, nullable=False, server_default=text("'habilidade'::text")))
    descricao: str = Field(sa_column=Column('descricao', Text, nullable=False))
    mecanica: Optional[dict] = Field(default=None, sa_column=Column('mecanica', JSONB, server_default=text("'{}'::jsonb")))
    gera_maestria: Optional[bool] = Field(default=None, sa_column=Column('gera_maestria', Boolean, server_default=text('false')))
    habilidade_maestria_padrao: Optional[str] = Field(default=None, sa_column=Column('habilidade_maestria_padrao', Text))
    escala_com_nivel: Optional[bool] = Field(default=None, sa_column=Column('escala_com_nivel', Boolean, server_default=text('false')))
    escala_descricao: Optional[str] = Field(default=None, sa_column=Column('escala_descricao', Text))
    requer_caminho: Optional[bool] = Field(default=None, sa_column=Column('requer_caminho', Boolean, server_default=text('false')))
    substituido_em: Optional[int] = Field(default=None, sa_column=Column('substituido_em', Integer))
    criado_em: Optional[datetime.datetime] = Field(default=None, sa_column=Column('criado_em', DateTime, server_default=text('now()')))

    vocacao: 'RefVocacoes' = Relationship(back_populates='habilidades')
'''


def main() -> int:
    if not MODELS.exists():
        print("[ERRO] models.py nao encontrado.")
        return 1

    c = MODELS.read_text(encoding="utf-8")
    antes = len(c)

    if SENTINELA in c:
        print(f"  [IDEMPOTENTE] Classes ja existem. Tamanho: {antes} bytes")
        return 0

    novo = c.rstrip() + NOVAS_CLASSES + "\n"
    MODELS.write_text(novo, encoding="utf-8")
    depois = len(novo)

    print("=" * 72)
    print(f"  [OK] 3 classes de vocacoes adicionadas.")
    print(f"  Antes: {antes} bytes | Depois: {depois} bytes (+{depois - antes})")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())