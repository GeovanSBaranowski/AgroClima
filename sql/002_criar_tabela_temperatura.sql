CREATE SCHEMA IF NOT EXISTS silver;

CREATE TABLE silver.temperatura_diaria(
    data_observacao DATE NOT NULL,
    latitude NUMERIC(9,6) NOT NULL CONSTRAINT latitude_valida CHECK (latitude >= -90 AND latitude <= 90),
    longitude NUMERIC(9,6) NOT NULL CONSTRAINT longitude_valida CHECK (longitude >= -180 AND longitude <= 180),
    temperatura_c DOUBLE PRECISION,
    fonte TEXT NOT NULL,
    referencia_temporal TEXT NOT NULL CONSTRAINT referencia_valida CHECK (referencia_temporal IN('UTC','LST')),
    arquivo_origem TEXT NOT NULL,
    carregado_em TIMESTAMPZ NOT NULL DEFAULT CURRENT_TIMESTAMP

    CONSTRAINT temperatura_diaria_pk PRIMARY KEY(
        data_observacao,
        latitude,
        longitude,
        fonte,
        referencia_temporal
    )
);