CREATE TABLE IF NOT EXISTS silver.cena_satelite (
    colecao TEXT NOT NULL,
    id_cena TEXT NOT NULL,
    data_hora_observacao TIMESTAMPTZ NOT NULL,
    plataforma TEXT,
    nuvens_cena_percentual DOUBLE PRECISION,
    url_visual TEXT NOT NULL,
    url_classificacao TEXT NOT NULL,
    arquivo_origem TEXT NOT NULL,
    carregado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT cena_satelite_pk
        PRIMARY KEY (colecao, id_cena),

    CONSTRAINT cena_satelite_nuvens_validas
        CHECK (
            nuvens_cena_percentual >= 0
            AND nuvens_cena_percentual <= 100
        )
);