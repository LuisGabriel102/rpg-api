from typing import Any, Optional
import datetime
import decimal

from sqlalchemy import ARRAY, Boolean, CheckConstraint, Column, DateTime, ForeignKeyConstraint, Index, Integer, Numeric, PrimaryKeyConstraint, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql.sqltypes import NullType
from sqlmodel import Field, Relationship, SQLModel

class Npcs(SQLModel, table=True):
    __table_args__ = (
        CheckConstraint('abertura >= 0 AND abertura <= 100', name='npcs_abertura_check'),
        CheckConstraint('amabilidade >= 0 AND amabilidade <= 100', name='npcs_amabilidade_check'),
        CheckConstraint('camada = ANY (ARRAY[1, 2, 3])', name='npcs_camada_check'),
        CheckConstraint('conscienciosidade >= 0 AND conscienciosidade <= 100', name='npcs_conscienciosidade_check'),
        CheckConstraint('extroversao >= 0 AND extroversao <= 100', name='npcs_extroversao_check'),
        CheckConstraint('idade_aparente > 0', name='npcs_idade_aparente_check'),
        CheckConstraint('neuroticismo >= 0 AND neuroticismo <= 100', name='npcs_neuroticismo_check'),
        CheckConstraint("sexo = ANY (ARRAY['masculino'::text, 'feminino'::text, 'nao_binario'::text, 'desconhecido'::text])", name='npcs_sexo_check'),
        CheckConstraint('singularidade >= 1 AND singularidade <= 10', name='npcs_singularidade_check'),
        CheckConstraint("status = ANY (ARRAY['vivo'::text, 'morto'::text, 'desaparecido'::text, 'exilado'::text])", name='npcs_status_check'),
        PrimaryKeyConstraint('id', name='npcs_pkey'),
        Index('idx_npcs_camada', 'camada', 'status'),
        Index('idx_npcs_localizacao', 'localizacao_atual'),
        Index('idx_npcs_nome_trgm', 'nome', postgresql_ops={'nome': 'gin_trgm_ops'}, postgresql_using='gin')
    )

    id: int = Field(sa_column=Column('id', Integer, primary_key=True))
    nome: str = Field(sa_column=Column('nome', Text, nullable=False))
    nome_curto: str = Field(sa_column=Column('nome_curto', Text, nullable=False))
    raca: str = Field(sa_column=Column('raca', Text, nullable=False, server_default=text("'humano'::text")))
    status: str = Field(sa_column=Column('status', Text, nullable=False, server_default=text("'vivo'::text")))
    camada: int = Field(sa_column=Column('camada', Integer, nullable=False, server_default=text('2')))
    personality_summary: str = Field(sa_column=Column('personality_summary', Text, nullable=False, server_default=text("''::text")))
    epiteto: Optional[str] = Field(default=None, sa_column=Column('epiteto', Text))
    sexo: Optional[str] = Field(default=None, sa_column=Column('sexo', Text))
    idade_aparente: Optional[int] = Field(default=None, sa_column=Column('idade_aparente', Integer))
    idade_real: Optional[int] = Field(default=None, sa_column=Column('idade_real', Integer))
    localizacao_atual: Optional[str] = Field(default=None, sa_column=Column('localizacao_atual', Text))
    localizacao_base: Optional[str] = Field(default=None, sa_column=Column('localizacao_base', Text))
    profissao: Optional[str] = Field(default=None, sa_column=Column('profissao', Text))
    facoes: Optional[list[str]] = Field(default=None, sa_column=Column('facoes', ARRAY(Text())))
    imagem_url: Optional[str] = Field(default=None, sa_column=Column('imagem_url', Text))
    abertura: Optional[int] = Field(default=None, sa_column=Column('abertura', Integer))
    conscienciosidade: Optional[int] = Field(default=None, sa_column=Column('conscienciosidade', Integer))
    extroversao: Optional[int] = Field(default=None, sa_column=Column('extroversao', Integer))
    amabilidade: Optional[int] = Field(default=None, sa_column=Column('amabilidade', Integer))
    neuroticismo: Optional[int] = Field(default=None, sa_column=Column('neuroticismo', Integer))
    valores: Optional[list[str]] = Field(default=None, sa_column=Column('valores', ARRAY(Text())))
    medo_principal: Optional[str] = Field(default=None, sa_column=Column('medo_principal', Text))
    medos_secundarios: Optional[list[str]] = Field(default=None, sa_column=Column('medos_secundarios', ARRAY(Text())))
    desejo_oculto: Optional[str] = Field(default=None, sa_column=Column('desejo_oculto', Text))
    linha_que_nao_cruza: Optional[str] = Field(default=None, sa_column=Column('linha_que_nao_cruza', Text))
    maior_arrependimento: Optional[str] = Field(default=None, sa_column=Column('maior_arrependimento', Text))
    estilo_de_fala: Optional[str] = Field(default=None, sa_column=Column('estilo_de_fala', Text))
    prompt_identidade: Optional[str] = Field(default=None, sa_column=Column('prompt_identidade', Text))
    prompt_dialogo: Optional[str] = Field(default=None, sa_column=Column('prompt_dialogo', Text))
    prompt_contexto_protagonista: Optional[str] = Field(default=None, sa_column=Column('prompt_contexto_protagonista', Text))
    tensao_interna: Optional[str] = Field(default=None, sa_column=Column('tensao_interna', Text))
    backstory_completa: Optional[str] = Field(default=None, sa_column=Column('backstory_completa', Text))
    backstory_resumida: Optional[str] = Field(default=None, sa_column=Column('backstory_resumida', Text))
    evento_formativo: Optional[str] = Field(default=None, sa_column=Column('evento_formativo', Text))
    notas_do_gpt: Optional[str] = Field(default=None, sa_column=Column('notas_do_gpt', Text))
    singularidade: Optional[int] = Field(default=None, sa_column=Column('singularidade', Integer))
    o_que_so_ele_pode_fazer: Optional[str] = Field(default=None, sa_column=Column('o_que_so_ele_pode_fazer', Text))
    momento_de_singularidade: Optional[str] = Field(default=None, sa_column=Column('momento_de_singularidade', Text))
    criado_em: Optional[datetime.datetime] = Field(default=None, sa_column=Column('criado_em', DateTime, server_default=text('now()')))
    atualizado_em: Optional[datetime.datetime] = Field(default=None, sa_column=Column('atualizado_em', DateTime, server_default=text('now()')))

    location_npcs: list['LocationNpcs'] = Relationship(back_populates='npc')


class RefBiomas(SQLModel, table=True):
    __tablename__ = 'ref_biomas'
    __table_args__ = (
        CheckConstraint("identidade_climatica = ANY (ARRAY['temperado'::text, 'tropical'::text, 'selvagem'::text, 'aberrante'::text])", name='ref_biomas_identidade_climatica_check'),
        PrimaryKeyConstraint('id', name='ref_biomas_pkey'),
        UniqueConstraint('nome', name='ref_biomas_nome_key')
    )

    id: int = Field(sa_column=Column('id', Integer, primary_key=True))
    nome: str = Field(sa_column=Column('nome', Text, nullable=False))
    nome_ptbr: str = Field(sa_column=Column('nome_ptbr', Text, nullable=False))
    identidade_climatica: str = Field(sa_column=Column('identidade_climatica', Text, nullable=False))
    criado_em: datetime.datetime = Field(sa_column=Column('criado_em', DateTime, nullable=False, server_default=text('now()')))
    atualizado_em: datetime.datetime = Field(sa_column=Column('atualizado_em', DateTime, nullable=False, server_default=text('now()')))
    temperatura_media: Optional[str] = Field(default=None, sa_column=Column('temperatura_media', Text))
    umidade: Optional[str] = Field(default=None, sa_column=Column('umidade', Text))
    descricao: Optional[str] = Field(default=None, sa_column=Column('descricao', Text))
    perigos_naturais: Optional[list[str]] = Field(default=None, sa_column=Column('perigos_naturais', ARRAY(Text())))
    fauna_tipica: Optional[list[str]] = Field(default=None, sa_column=Column('fauna_tipica', ARRAY(Text())))
    flora_tipica: Optional[list[str]] = Field(default=None, sa_column=Column('flora_tipica', ARRAY(Text())))
    metadata_: Optional[dict] = Field(default=None, sa_column=Column('metadata', JSONB, server_default=text("'{}'::jsonb")))

    regions: list['Regions'] = Relationship(back_populates='bioma')


class RefLocais(SQLModel, table=True):
    __tablename__ = 'ref_locais'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='ref_locais_pkey'),
        UniqueConstraint('nome', name='uq_locais_nome'),
        Index('idx_locais_1492', 'relevante_1492'),
        Index('idx_locais_regiao', 'regiao'),
        Index('idx_locais_tipo', 'tipo')
    )

    id: int = Field(sa_column=Column('id', Integer, primary_key=True))
    nome: str = Field(sa_column=Column('nome', Text, nullable=False))
    nome_ptbr: str = Field(sa_column=Column('nome_ptbr', Text, nullable=False))
    regiao: Optional[str] = Field(default=None, sa_column=Column('regiao', Text))
    tipo: Optional[str] = Field(default=None, sa_column=Column('tipo', Text))
    pais: Optional[str] = Field(default=None, sa_column=Column('pais', Text))
    descricao: Optional[str] = Field(default=None, sa_column=Column('descricao', Text))
    populacao_aprox: Optional[int] = Field(default=None, sa_column=Column('populacao_aprox', Integer))
    faccoes_presentes: Optional[list[str]] = Field(default=None, sa_column=Column('faccoes_presentes', ARRAY(Text())))
    perigos_tipicos: Optional[list[str]] = Field(default=None, sa_column=Column('perigos_tipicos', ARRAY(Text())))
    clima_predominante: Optional[str] = Field(default=None, sa_column=Column('clima_predominante', Text))
    imagem_url: Optional[str] = Field(default=None, sa_column=Column('imagem_url', Text))
    relevante_1492: Optional[bool] = Field(default=None, sa_column=Column('relevante_1492', Boolean, server_default=text('true')))
    coordenadas_narrativas: Optional[str] = Field(default=None, sa_column=Column('coordenadas_narrativas', Text))
    notas_gpt: Optional[str] = Field(default=None, sa_column=Column('notas_gpt', Text))
    criado_em: Optional[datetime.datetime] = Field(default=None, sa_column=Column('criado_em', DateTime, server_default=text('now()')))

    locations: list['Locations'] = Relationship(back_populates='legacy_local')


class Worlds(SQLModel, table=True):
    __table_args__ = (
        CheckConstraint("status = ANY (ARRAY['ativo'::text, 'arquivado'::text, 'rascunho'::text])", name='worlds_status_check'),
        PrimaryKeyConstraint('id', name='worlds_pkey')
    )

    id: int = Field(sa_column=Column('id', Integer, primary_key=True))
    nome: str = Field(sa_column=Column('nome', Text, nullable=False))
    status: str = Field(sa_column=Column('status', Text, nullable=False, server_default=text("'ativo'::text")))
    criado_em: datetime.datetime = Field(sa_column=Column('criado_em', DateTime, nullable=False, server_default=text('now()')))
    atualizado_em: datetime.datetime = Field(sa_column=Column('atualizado_em', DateTime, nullable=False, server_default=text('now()')))
    nome_display: Optional[str] = Field(default=None, sa_column=Column('nome_display', Text))
    descricao: Optional[str] = Field(default=None, sa_column=Column('descricao', Text))
    metadata_: Optional[dict] = Field(default=None, sa_column=Column('metadata', JSONB, server_default=text("'{}'::jsonb")))

    continents: list['Continents'] = Relationship(back_populates='world')
    regions: list['Regions'] = Relationship(back_populates='world')
    locations: list['Locations'] = Relationship(back_populates='world')


class Continents(SQLModel, table=True):
    __table_args__ = (
        CheckConstraint('coastline_stability >= 0::numeric AND coastline_stability <= 10::numeric', name='continents_coastline_stability_check'),
        CheckConstraint("identidade_climatica = ANY (ARRAY['temperado'::text, 'tropical'::text, 'selvagem'::text, 'aberrante'::text])", name='continents_identidade_climatica_check'),
        CheckConstraint("tier_conhecimento = ANY (ARRAY['conhecido'::text, 'rumores'::text, 'desconhecido'::text])", name='continents_tier_conhecimento_check'),
        ForeignKeyConstraint(['world_id'], ['worlds.id'], name='continents_world_id_fkey'),
        PrimaryKeyConstraint('id', name='continents_pkey'),
        UniqueConstraint('world_id', 'nome', name='continents_world_id_nome_key'),
        Index('idx_continents_clima', 'identidade_climatica'),
        Index('idx_continents_tier', 'world_id', 'tier_conhecimento'),
        Index('idx_continents_world', 'world_id')
    )

    id: int = Field(sa_column=Column('id', Integer, primary_key=True))
    world_id: int = Field(sa_column=Column('world_id', Integer, nullable=False))
    nome: str = Field(sa_column=Column('nome', Text, nullable=False))
    identidade_climatica: str = Field(sa_column=Column('identidade_climatica', Text, nullable=False))
    tier_conhecimento: str = Field(sa_column=Column('tier_conhecimento', Text, nullable=False, server_default=text("'desconhecido'::text")))
    is_parasita: bool = Field(sa_column=Column('is_parasita', Boolean, nullable=False, server_default=text('false')))
    geometria_estavel: bool = Field(sa_column=Column('geometria_estavel', Boolean, nullable=False, server_default=text('true')))
    criado_em: datetime.datetime = Field(sa_column=Column('criado_em', DateTime, nullable=False, server_default=text('now()')))
    atualizado_em: datetime.datetime = Field(sa_column=Column('atualizado_em', DateTime, nullable=False, server_default=text('now()')))
    nome_ptbr: Optional[str] = Field(default=None, sa_column=Column('nome_ptbr', Text))
    descricao: Optional[str] = Field(default=None, sa_column=Column('descricao', Text))
    descricao_publica: Optional[str] = Field(default=None, sa_column=Column('descricao_publica', Text))
    area_relativa: Optional[str] = Field(default=None, sa_column=Column('area_relativa', Text))
    populacao_estimada: Optional[str] = Field(default=None, sa_column=Column('populacao_estimada', Text))
    posicao_cardeal: Optional[str] = Field(default=None, sa_column=Column('posicao_cardeal', Text))
    coastline_stability: Optional[decimal.Decimal] = Field(default=None, sa_column=Column('coastline_stability', Numeric(3, 1), server_default=text('10.0')))
    last_surveyed: Optional[datetime.datetime] = Field(default=None, sa_column=Column('last_surveyed', DateTime))
    metadata_: Optional[dict] = Field(default=None, sa_column=Column('metadata', JSONB, server_default=text("'{}'::jsonb")))
    imagem_url: Optional[str] = Field(default=None, sa_column=Column('imagem_url', Text))
    embedding: Optional[Any] = Field(default=None, sa_column=Column('embedding', NullType))

    world: 'Worlds' = Relationship(back_populates='continents')
    regions: list['Regions'] = Relationship(back_populates='continent')


class Regions(SQLModel, table=True):
    __table_args__ = (
        CheckConstraint('estabilidade_temporal >= 0::numeric AND estabilidade_temporal <= 10::numeric', name='regions_estabilidade_temporal_check'),
        CheckConstraint('nivel_perigo >= 1 AND nivel_perigo <= 10', name='regions_nivel_perigo_check'),
        CheckConstraint("tier_conhecimento = ANY (ARRAY['conhecido'::text, 'rumores'::text, 'desconhecido'::text])", name='regions_tier_conhecimento_check'),
        CheckConstraint("tipo_regiao = ANY (ARRAY['reino'::text, 'provincia'::text, 'regiao'::text, 'distrito'::text, 'territorio'::text, 'zona_selvagem'::text, 'zona_aberrante'::text])", name='regions_tipo_regiao_check'),
        ForeignKeyConstraint(['bioma_id'], ['ref_biomas.id'], name='regions_bioma_id_fkey'),
        ForeignKeyConstraint(['continent_id'], ['continents.id'], name='regions_continent_id_fkey'),
        ForeignKeyConstraint(['parent_region_id'], ['regions.id'], name='regions_parent_region_id_fkey'),
        ForeignKeyConstraint(['world_id'], ['worlds.id'], name='regions_world_id_fkey'),
        PrimaryKeyConstraint('id', name='regions_pkey'),
        UniqueConstraint('world_id', 'continent_id', 'nome', name='regions_world_id_continent_id_nome_key'),
        Index('idx_regions_bioma', 'bioma_id'),
        Index('idx_regions_continent', 'continent_id'),
        Index('idx_regions_metadata', 'metadata', postgresql_ops={'metadata': 'jsonb_path_ops'}, postgresql_using='gin'),
        Index('idx_regions_parent', 'parent_region_id'),
        Index('idx_regions_path', 'path', postgresql_using='gist'),
        Index('idx_regions_perigo', 'nivel_perigo'),
        Index('idx_regions_tier', 'world_id', 'tier_conhecimento'),
        Index('idx_regions_tipo', 'tipo_regiao'),
        Index('idx_regions_world', 'world_id')
    )

    id: int = Field(sa_column=Column('id', Integer, primary_key=True))
    world_id: int = Field(sa_column=Column('world_id', Integer, nullable=False))
    continent_id: int = Field(sa_column=Column('continent_id', Integer, nullable=False))
    nome: str = Field(sa_column=Column('nome', Text, nullable=False))
    tipo_regiao: str = Field(sa_column=Column('tipo_regiao', Text, nullable=False, server_default=text("'reino'::text")))
    tier_conhecimento: str = Field(sa_column=Column('tier_conhecimento', Text, nullable=False, server_default=text("'desconhecido'::text")))
    geometria_estavel: bool = Field(sa_column=Column('geometria_estavel', Boolean, nullable=False, server_default=text('true')))
    criado_em: datetime.datetime = Field(sa_column=Column('criado_em', DateTime, nullable=False, server_default=text('now()')))
    atualizado_em: datetime.datetime = Field(sa_column=Column('atualizado_em', DateTime, nullable=False, server_default=text('now()')))
    parent_region_id: Optional[int] = Field(default=None, sa_column=Column('parent_region_id', Integer))
    path: Optional[Any] = Field(default=None, sa_column=Column('path', NullType))
    nome_ptbr: Optional[str] = Field(default=None, sa_column=Column('nome_ptbr', Text))
    bioma_id: Optional[int] = Field(default=None, sa_column=Column('bioma_id', Integer))
    descricao: Optional[str] = Field(default=None, sa_column=Column('descricao', Text))
    descricao_publica: Optional[str] = Field(default=None, sa_column=Column('descricao_publica', Text))
    populacao_estimada: Optional[str] = Field(default=None, sa_column=Column('populacao_estimada', Text))
    nivel_perigo: Optional[int] = Field(default=None, sa_column=Column('nivel_perigo', Integer, server_default=text('1')))
    governante: Optional[str] = Field(default=None, sa_column=Column('governante', Text))
    recursos_naturais: Optional[list[str]] = Field(default=None, sa_column=Column('recursos_naturais', ARRAY(Text())))
    rotas_comerciais: Optional[list[str]] = Field(default=None, sa_column=Column('rotas_comerciais', ARRAY(Text())))
    estabilidade_temporal: Optional[decimal.Decimal] = Field(default=None, sa_column=Column('estabilidade_temporal', Numeric(3, 1), server_default=text('10.0')))
    traversal_rules: Optional[dict] = Field(default=None, sa_column=Column('traversal_rules', JSONB))
    metadata_: Optional[dict] = Field(default=None, sa_column=Column('metadata', JSONB, server_default=text("'{}'::jsonb")))
    imagem_url: Optional[str] = Field(default=None, sa_column=Column('imagem_url', Text))
    embedding: Optional[Any] = Field(default=None, sa_column=Column('embedding', NullType))

    bioma: Optional['RefBiomas'] = Relationship(back_populates='regions')
    continent: 'Continents' = Relationship(back_populates='regions')
    parent_region: Optional['Regions'] = Relationship(back_populates='parent_region_reverse', sa_relationship_kwargs={'remote_side': '[Regions.id]'})
    parent_region_reverse: list['Regions'] = Relationship(back_populates='parent_region', sa_relationship_kwargs={'remote_side': '[Regions.parent_region_id]'})
    world: 'Worlds' = Relationship(back_populates='regions')
    locations: list['Locations'] = Relationship(back_populates='region')


class Locations(SQLModel, table=True):
    __table_args__ = (
        CheckConstraint('geometry_stability >= 0::numeric AND geometry_stability <= 10::numeric', name='locations_geometry_stability_check'),
        CheckConstraint('nivel_perigo >= 1 AND nivel_perigo <= 10', name='locations_nivel_perigo_check'),
        CheckConstraint("tier_conhecimento = ANY (ARRAY['conhecido'::text, 'rumores'::text, 'desconhecido'::text])", name='locations_tier_conhecimento_check'),
        CheckConstraint("tipo_local = ANY (ARRAY['capital'::text, 'cidade'::text, 'vila'::text, 'povoado'::text, 'fortaleza'::text, 'ruina'::text, 'dungeon'::text, 'ponto_interesse'::text, 'porto'::text, 'templo'::text, 'torre'::text, 'acampamento'::text, 'caverna'::text, 'monumento'::text, 'portal'::text, 'anomalia'::text, 'selvagem'::text])", name='locations_tipo_local_check'),
        ForeignKeyConstraint(['legacy_local_id'], ['ref_locais.id'], name='locations_legacy_local_id_fkey'),
        ForeignKeyConstraint(['region_id'], ['regions.id'], name='locations_region_id_fkey'),
        ForeignKeyConstraint(['world_id'], ['worlds.id'], name='locations_world_id_fkey'),
        PrimaryKeyConstraint('id', name='locations_pkey'),
        UniqueConstraint('world_id', 'region_id', 'nome', name='locations_world_id_region_id_nome_key'),
        Index('idx_locations_coords', 'coord_x', 'coord_y'),
        Index('idx_locations_legacy', 'legacy_local_id', postgresql_where='(legacy_local_id IS NOT NULL)'),
        Index('idx_locations_metadata', 'metadata', postgresql_ops={'metadata': 'jsonb_path_ops'}, postgresql_using='gin'),
        Index('idx_locations_perigo', 'nivel_perigo'),
        Index('idx_locations_region', 'region_id'),
        Index('idx_locations_servicos', 'servicos_disponiveis', postgresql_using='gin'),
        Index('idx_locations_tier', 'world_id', 'tier_conhecimento'),
        Index('idx_locations_tipo', 'tipo_local'),
        Index('idx_locations_world', 'world_id')
    )

    id: int = Field(sa_column=Column('id', Integer, primary_key=True))
    world_id: int = Field(sa_column=Column('world_id', Integer, nullable=False))
    region_id: int = Field(sa_column=Column('region_id', Integer, nullable=False))
    nome: str = Field(sa_column=Column('nome', Text, nullable=False))
    tipo_local: str = Field(sa_column=Column('tipo_local', Text, nullable=False, server_default=text("'povoado'::text")))
    tier_conhecimento: str = Field(sa_column=Column('tier_conhecimento', Text, nullable=False, server_default=text("'desconhecido'::text")))
    geometria_estavel: bool = Field(sa_column=Column('geometria_estavel', Boolean, nullable=False, server_default=text('true')))
    criado_em: datetime.datetime = Field(sa_column=Column('criado_em', DateTime, nullable=False, server_default=text('now()')))
    atualizado_em: datetime.datetime = Field(sa_column=Column('atualizado_em', DateTime, nullable=False, server_default=text('now()')))
    legacy_local_id: Optional[int] = Field(default=None, sa_column=Column('legacy_local_id', Integer))
    nome_ptbr: Optional[str] = Field(default=None, sa_column=Column('nome_ptbr', Text))
    descricao: Optional[str] = Field(default=None, sa_column=Column('descricao', Text))
    descricao_publica: Optional[str] = Field(default=None, sa_column=Column('descricao_publica', Text))
    coord_x: Optional[decimal.Decimal] = Field(default=None, sa_column=Column('coord_x', Numeric(8, 2)))
    coord_y: Optional[decimal.Decimal] = Field(default=None, sa_column=Column('coord_y', Numeric(8, 2)))
    populacao_aprox: Optional[int] = Field(default=None, sa_column=Column('populacao_aprox', Integer))
    nivel_perigo: Optional[int] = Field(default=None, sa_column=Column('nivel_perigo', Integer, server_default=text('1')))
    governante: Optional[str] = Field(default=None, sa_column=Column('governante', Text))
    faccoes_presentes: Optional[list[str]] = Field(default=None, sa_column=Column('faccoes_presentes', ARRAY(Text())))
    perigos_tipicos: Optional[list[str]] = Field(default=None, sa_column=Column('perigos_tipicos', ARRAY(Text())))
    servicos_disponiveis: Optional[list[str]] = Field(default=None, sa_column=Column('servicos_disponiveis', ARRAY(Text())))
    clima_predominante: Optional[str] = Field(default=None, sa_column=Column('clima_predominante', Text))
    geometry_stability: Optional[decimal.Decimal] = Field(default=None, sa_column=Column('geometry_stability', Numeric(3, 1), server_default=text('10.0')))
    contradicoes_cartograficas: Optional[list[str]] = Field(default=None, sa_column=Column('contradicoes_cartograficas', ARRAY(Text())))
    metadata_: Optional[dict] = Field(default=None, sa_column=Column('metadata', JSONB, server_default=text("'{}'::jsonb")))
    notas_gpt: Optional[str] = Field(default=None, sa_column=Column('notas_gpt', Text))
    imagem_url: Optional[str] = Field(default=None, sa_column=Column('imagem_url', Text))
    embedding: Optional[Any] = Field(default=None, sa_column=Column('embedding', NullType))

    legacy_local: Optional['RefLocais'] = Relationship(back_populates='locations')
    region: 'Regions' = Relationship(back_populates='locations')
    world: 'Worlds' = Relationship(back_populates='locations')
    location_npcs: list['LocationNpcs'] = Relationship(back_populates='location')


class LocationNpcs(SQLModel, table=True):
    __tablename__ = 'location_npcs'
    __table_args__ = (
        CheckConstraint("tipo_presenca = ANY (ARRAY['residente'::text, 'visitante'::text, 'preso'::text, 'governante'::text, 'comerciante'::text, 'oculto'::text, 'itinerante'::text, 'morto_aqui'::text])", name='location_npcs_tipo_presenca_check'),
        ForeignKeyConstraint(['location_id'], ['locations.id'], ondelete='CASCADE', name='location_npcs_location_id_fkey'),
        ForeignKeyConstraint(['npc_id'], ['npcs.id'], ondelete='CASCADE', name='location_npcs_npc_id_fkey'),
        PrimaryKeyConstraint('id', name='location_npcs_pkey'),
        UniqueConstraint('location_id', 'npc_id', name='location_npcs_location_id_npc_id_key'),
        Index('idx_ln_location', 'location_id'),
        Index('idx_ln_npc', 'npc_id')
    )

    id: int = Field(sa_column=Column('id', Integer, primary_key=True))
    location_id: int = Field(sa_column=Column('location_id', Integer, nullable=False))
    npc_id: int = Field(sa_column=Column('npc_id', Integer, nullable=False))
    criado_em: datetime.datetime = Field(sa_column=Column('criado_em', DateTime, nullable=False, server_default=text('now()')))
    tipo_presenca: Optional[str] = Field(default=None, sa_column=Column('tipo_presenca', Text, server_default=text("'residente'::text")))
    horario_presenca: Optional[str] = Field(default=None, sa_column=Column('horario_presenca', Text))
    descricao: Optional[str] = Field(default=None, sa_column=Column('descricao', Text))

    location: 'Locations' = Relationship(back_populates='location_npcs')
    npc: 'Npcs' = Relationship(back_populates='location_npcs')


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


# === PILARES (Modulo 6.4) ===

class RefPilares(SQLModel, table=True):
    __tablename__ = 'ref_pilares'
    __table_args__ = (
        PrimaryKeyConstraint('nome', name='ref_pilares_pkey'),
    )

    nome: str = Field(sa_column=Column('nome', Text, primary_key=True))
    epiteto: str = Field(sa_column=Column('epiteto', Text, nullable=False))
    filosofia: str = Field(sa_column=Column('filosofia', Text, nullable=False))
    criado_em: Optional[datetime.datetime] = Field(default=None, sa_column=Column('criado_em', DateTime, server_default=text('now()')))

