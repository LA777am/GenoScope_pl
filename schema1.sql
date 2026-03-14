-- GenoScope Database Schema (Sanitized / Public Version)
-- PostgreSQL 16+



SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;

SET default_tablespace = '';
SET default_table_access_method = heap;

-- =============================================
-- Table: analyses
-- =============================================
CREATE TABLE public.analyses (
    analysis_id integer NOT NULL,
    sequence_id integer NOT NULL,
    analysis_type character varying(50) NOT NULL,
    results jsonb NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE public.analyses_analysis_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.analyses_analysis_id_seq OWNED BY public.analyses.analysis_id;

ALTER TABLE public.analyses
    ADD CONSTRAINT analyses_pkey PRIMARY KEY (analysis_id);

-- =============================================
-- Table: analysis_history
-- =============================================
CREATE TABLE public.analysis_history (
    id integer NOT NULL,
    user_id integer,
    sequence text NOT NULL,
    analysis_type character varying(50) NOT NULL,
    result_json jsonb NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    sequence_id integer
);

CREATE SEQUENCE public.analysis_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.analysis_history_id_seq OWNED BY public.analysis_history.id;

ALTER TABLE public.analysis_history
    ADD CONSTRAINT analysis_history_pkey PRIMARY KEY (id);

-- =============================================
-- Table: batch_history
-- =============================================
CREATE TABLE public.batch_history (
    id integer NOT NULL,
    user_id integer,
    batch_id integer,
    analysis_type character varying(50) NOT NULL,
    summary_json jsonb NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE public.batch_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.batch_history_id_seq OWNED BY public.batch_history.id;

ALTER TABLE public.batch_history
    ADD CONSTRAINT batch_history_pkey PRIMARY KEY (id);

-- =============================================
-- Table: batches
-- =============================================
CREATE TABLE public.batches (
    batch_id integer NOT NULL,
    batch_name character varying(100) NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    user_id integer
);

CREATE SEQUENCE public.batches_batch_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.batches_batch_id_seq OWNED BY public.batches.batch_id;

ALTER TABLE public.batches
    ADD CONSTRAINT batches_pkey PRIMARY KEY (batch_id);

-- =============================================
-- Table: comparisons
-- =============================================
CREATE TABLE public.comparisons (
    comparison_id integer NOT NULL,
    metrics jsonb NOT NULL,
    final_score double precision,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    user_id integer
);

CREATE SEQUENCE public.comparisons_comparison_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.comparisons_comparison_id_seq OWNED BY public.comparisons.comparison_id;

ALTER TABLE public.comparisons
    ADD CONSTRAINT comparisons_pkey PRIMARY KEY (comparison_id);

-- =============================================
-- Table: predictions
-- =============================================
CREATE TABLE public.predictions (
    prediction_id integer NOT NULL,
    sequence_id integer NOT NULL,
    model_type character varying(20) NOT NULL,
    predicted_label character varying(50) NOT NULL,
    confidence double precision,
    features_used jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT predictions_confidence_check CHECK ((confidence >= 0 AND confidence <= 1))
);

CREATE SEQUENCE public.predictions_prediction_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.predictions_prediction_id_seq OWNED BY public.predictions.prediction_id;

ALTER TABLE public.predictions
    ADD CONSTRAINT predictions_pkey PRIMARY KEY (prediction_id);

-- =============================================
-- Table: sequences
-- =============================================
CREATE TABLE public.sequences (
    sequence_id integer NOT NULL,
    batch_id integer NOT NULL,
    raw_sequence text NOT NULL,
    cleaned_sequence text NOT NULL,
    length integer NOT NULL,
    gc_percent double precision,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    user_id integer
);

CREATE SEQUENCE public.sequences_sequence_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.sequences_sequence_id_seq OWNED BY public.sequences.sequence_id;

ALTER TABLE public.sequences
    ADD CONSTRAINT sequences_pkey PRIMARY KEY (sequence_id);

-- =============================================
-- Table: users
-- =============================================
CREATE TABLE public.users (
    user_id integer NOT NULL,
    username text NOT NULL,
    password_hash text NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE public.users_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.users_user_id_seq OWNED BY public.users.user_id;

ALTER TABLE public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);

ALTER TABLE public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);

-- =============================================
-- Foreign Keys
-- =============================================

ALTER TABLE public.analysis_history
    ADD CONSTRAINT analysis_history_sequence_id_fkey FOREIGN KEY (sequence_id) REFERENCES public.sequences(sequence_id);

ALTER TABLE public.analysis_history
    ADD CONSTRAINT analysis_history_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;

ALTER TABLE public.batch_history
    ADD CONSTRAINT batch_history_batch_id_fkey FOREIGN KEY (batch_id) REFERENCES public.batches(batch_id) ON DELETE CASCADE;

ALTER TABLE public.batch_history
    ADD CONSTRAINT batch_history_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;

ALTER TABLE public.batches
    ADD CONSTRAINT batches_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);

ALTER TABLE public.comparisons
    ADD CONSTRAINT comparisons_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;

ALTER TABLE public.sequences
    ADD CONSTRAINT fk_batch FOREIGN KEY (batch_id) REFERENCES public.batches(batch_id) ON DELETE CASCADE;

ALTER TABLE public.analyses
    ADD CONSTRAINT fk_sequence_analysis FOREIGN KEY (sequence_id) REFERENCES public.sequences(sequence_id) ON DELETE CASCADE;

ALTER TABLE public.predictions
    ADD CONSTRAINT fk_sequence_prediction FOREIGN KEY (sequence_id) REFERENCES public.sequences(sequence_id) ON DELETE CASCADE;

ALTER TABLE public.sequences
    ADD CONSTRAINT sequences_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);

-- End of sanitized schema