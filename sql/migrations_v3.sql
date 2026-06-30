-- ============================================================
-- NEXUS RPG API v3 — SQL MIGRATIONS
-- Execute no pgAdmin conectado ao Railway Nexus
-- ============================================================

-- 001: EVENT SOURCING — Registra cada acao do jogo como evento imutavel
CREATE TABLE IF NOT EXISTS rpg_events (
    id SERIAL PRIMARY KEY,
    aggregate_type VARCHAR(50) NOT NULL,    -- personagem, combate, npc, campanha, sessao, dados
    aggregate_id INTEGER NOT NULL,
    event_type VARCHAR(100) NOT NULL,       -- DAMAGE_TAKEN, SPELL_CAST, LEVEL_UP, DICE_ROLL, etc.
    payload JSONB NOT NULL DEFAULT '{}',
    sessao_id INTEGER,
    personagem_id INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rpg_events_type ON rpg_events(event_type);
CREATE INDEX IF NOT EXISTS idx_rpg_events_aggregate ON rpg_events(aggregate_type, aggregate_id);
CREATE INDEX IF NOT EXISTS idx_rpg_events_sessao ON rpg_events(sessao_id);
CREATE INDEX IF NOT EXISTS idx_rpg_events_personagem ON rpg_events(personagem_id);
CREATE INDEX IF NOT EXISTS idx_rpg_events_created ON rpg_events(created_at DESC);


-- 002: SAVE POINTS — Snapshots nomeados do estado do personagem
CREATE TABLE IF NOT EXISTS player_save_points (
    id SERIAL PRIMARY KEY,
    personagem_id INTEGER NOT NULL,
    nome VARCHAR(200) NOT NULL,
    snapshot JSONB NOT NULL,
    sessao_id INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_save_points_personagem ON player_save_points(personagem_id);
CREATE INDEX IF NOT EXISTS idx_save_points_created ON player_save_points(created_at DESC);


-- 003: DETECTAR FOREIGN KEYS SEM INDICE
-- Execute esta query para encontrar FKs que precisam de indice:
/*
SELECT conrelid::regclass AS tabela,
       conname AS constraint_fk,
       pg_size_pretty(pg_relation_size(conrelid)) AS tamanho_tabela
FROM pg_constraint
JOIN pg_class ON (conrelid = pg_class.oid)
WHERE contype = 'f'
AND NOT EXISTS (
    SELECT 1 FROM pg_index
    WHERE indrelid = conrelid
    AND conkey <@ indkey AND conkey @> indkey
)
ORDER BY pg_relation_size(conrelid) DESC;
*/

-- Apos executar a query acima, crie indices para cada FK listada.
-- Exemplo:
-- CREATE INDEX idx_magias_raiz_id ON magias(raiz_id);
-- CREATE INDEX idx_personagem_condicoes_condicao_id ON personagem_condicoes(condicao_id);


-- 004: AUDIT TRIGGER (opcional — para tabelas criticas)
-- Crie se quiser auditoria automatica em tabelas como personagens, inventario
/*
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(10) NOT NULL,  -- INSERT, UPDATE, DELETE
    old_data JSONB,
    new_data JSONB,
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    changed_by VARCHAR(50) DEFAULT current_user
);

CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (table_name, operation, old_data)
        VALUES (TG_TABLE_NAME, 'DELETE', row_to_json(OLD)::jsonb);
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (table_name, operation, old_data, new_data)
        VALUES (TG_TABLE_NAME, 'UPDATE', row_to_json(OLD)::jsonb, row_to_json(NEW)::jsonb);
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (table_name, operation, new_data)
        VALUES (TG_TABLE_NAME, 'INSERT', row_to_json(NEW)::jsonb);
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Aplique em tabelas criticas:
-- CREATE TRIGGER audit_personagens AFTER INSERT OR UPDATE OR DELETE ON personagens FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
*/


-- 005: POSTGRESQL 18 — COLUNAS VIRTUAIS GERADAS (execute se usar PG18)
-- Modificadores calculados automaticamente, zero armazenamento
/*
ALTER TABLE personagens ADD COLUMN IF NOT EXISTS
    str_modifier INT GENERATED ALWAYS AS (FLOOR((forca - 10) / 2.0)) STORED;
ALTER TABLE personagens ADD COLUMN IF NOT EXISTS
    dex_modifier INT GENERATED ALWAYS AS (FLOOR((destreza - 10) / 2.0)) STORED;
ALTER TABLE personagens ADD COLUMN IF NOT EXISTS
    con_modifier INT GENERATED ALWAYS AS (FLOOR((constituicao - 10) / 2.0)) STORED;
ALTER TABLE personagens ADD COLUMN IF NOT EXISTS
    int_modifier INT GENERATED ALWAYS AS (FLOOR((inteligencia - 10) / 2.0)) STORED;
ALTER TABLE personagens ADD COLUMN IF NOT EXISTS
    wis_modifier INT GENERATED ALWAYS AS (FLOOR((sabedoria - 10) / 2.0)) STORED;
ALTER TABLE personagens ADD COLUMN IF NOT EXISTS
    cha_modifier INT GENERATED ALWAYS AS (FLOOR((carisma - 10) / 2.0)) STORED;
ALTER TABLE personagens ADD COLUMN IF NOT EXISTS
    bonus_proficiencia INT GENERATED ALWAYS AS (FLOOR((nivel - 1) / 4) + 2) STORED;
*/


-- 006: MATERIALIZED VIEW — Ficha completa pre-calculada
-- Atualizar com: REFRESH MATERIALIZED VIEW CONCURRENTLY mv_character_summary;
/*
CREATE MATERIALIZED VIEW mv_character_summary AS
SELECT p.id, p.nome, p.nivel, p.hp_atual, p.hp_maximo, p.mp_atual, p.mp_maximo,
       p.ca, p.forca, p.destreza, p.constituicao, p.inteligencia, p.sabedoria, p.carisma,
       FLOOR((p.forca - 10) / 2.0) AS str_mod,
       FLOOR((p.destreza - 10) / 2.0) AS dex_mod,
       FLOOR((p.constituicao - 10) / 2.0) AS con_mod,
       (SELECT COUNT(*) FROM personagem_condicoes pc WHERE pc.personagem_id = p.id) AS condicoes_ativas,
       (SELECT json_agg(rc.nome) FROM personagem_condicoes pc
        JOIN ref_condicoes rc ON pc.condicao_id = rc.id
        WHERE pc.personagem_id = p.id) AS nomes_condicoes
FROM personagens p;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_char_summary_id ON mv_character_summary(id);
*/


-- 007: LOCALE/i18n — Tabela de traducoes (futuro)
-- Para suportar portugues + ingles nas respostas da API
/*
CREATE TABLE IF NOT EXISTS spell_translations (
    id SERIAL PRIMARY KEY,
    spell_id INTEGER NOT NULL REFERENCES magias(id),
    locale VARCHAR(10) NOT NULL DEFAULT 'pt-BR',
    nome_traduzido TEXT,
    descricao_traduzida TEXT,
    UNIQUE(spell_id, locale)
);
*/
