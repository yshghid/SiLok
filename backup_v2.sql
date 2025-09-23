--
-- PostgreSQL database dump
--

\restrict aJKSm9umxmErXONQStTRINbCASV5jIuWYHIjEAaHF4b6gL6G1pG2UIa29SVO3DR

-- Dumped from database version 17.6 (Homebrew)
-- Dumped by pg_dump version 17.6 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pgaudit; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgaudit WITH SCHEMA public;


--
-- Name: EXTENSION pgaudit; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pgaudit IS 'provides auditing functionality';


--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


--
-- Name: cosine_similarity(public.vector, public.vector); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.cosine_similarity(v1 public.vector, v2 public.vector) RETURNS double precision
    LANGUAGE plpgsql IMMUTABLE
    AS $$
BEGIN
  -- pgvector의 <=> 는 코사인 거리(cosine distance)를 반환하므로
  -- 1 - 거리 = 코사인 유사도
  RETURN 1 - (v1 <=> v2);
END;
$$;


ALTER FUNCTION public.cosine_similarity(v1 public.vector, v2 public.vector) OWNER TO postgres;

--
-- Name: get_exec_time(text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_exec_time(query text) RETURNS double precision
    LANGUAGE plpgsql
    AS $$
DECLARE
    plan JSON;
    exec_time FLOAT;
BEGIN
    EXECUTE format('EXPLAIN (ANALYZE, FORMAT JSON) %s', query) INTO plan;
    exec_time := (plan->0->>'Execution Time')::FLOAT;
    RETURN exec_time;
END;
$$;


ALTER FUNCTION public.get_exec_time(query text) OWNER TO postgres;

--
-- Name: normalize_vector(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.normalize_vector() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
  norm FLOAT;
  zero_vec VECTOR(384);
BEGIN
  -- 384차원 영벡터 생성
  zero_vec := array_fill(0.0::float, ARRAY[384])::vector;

  -- L2 Norm 계산: 벡터와 영벡터 간의 L2 거리
  norm := NEW.embedding_vector <-> zero_vec;

  -- norm이 양수일 때만 정규화
  IF norm > 0 THEN
    NEW.embedding_vector := NEW.embedding_vector / norm;
  END IF;

  RETURN NEW;
END;
$$;


ALTER FUNCTION public.normalize_vector() OWNER TO postgres;

--
-- Name: random_vector(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.random_vector() RETURNS public.vector
    LANGUAGE sql
    AS $$
    SELECT array_agg(random())::vector(384)
    FROM generate_series(1,384);
$$;


ALTER FUNCTION public.random_vector() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: description; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.description (
    id integer NOT NULL,
    task_id bigint,
    content text,
    embedding public.vector(1536)
);


ALTER TABLE public.description OWNER TO postgres;

--
-- Name: description_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.description_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.description_id_seq OWNER TO postgres;

--
-- Name: description_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.description_id_seq OWNED BY public.description.id;


--
-- Name: employee; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.employee (
    id integer NOT NULL,
    name character varying(50) NOT NULL
);


ALTER TABLE public.employee OWNER TO postgres;

--
-- Name: notion; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.notion (
    id integer NOT NULL,
    task_id character varying(50),
    "timestamp" timestamp without time zone NOT NULL,
    participant_id character varying(50),
    content text
);


ALTER TABLE public.notion OWNER TO postgres;

--
-- Name: onedrive; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.onedrive (
    id integer NOT NULL,
    task_id character varying(50),
    "timestamp" timestamp without time zone NOT NULL,
    writer character varying(50),
    content text
);


ALTER TABLE public.onedrive OWNER TO postgres;

--
-- Name: outlook; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.outlook (
    id integer NOT NULL,
    receiver character varying(50),
    sender character varying(50) NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    task_id character varying(50),
    content text
);


ALTER TABLE public.outlook OWNER TO postgres;

--
-- Name: participant; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.participant (
    id integer NOT NULL,
    notion_id integer,
    p1 character varying(50),
    p2 character varying(50),
    p3 character varying(50),
    p4 character varying(50),
    p5 character varying(50),
    p6 character varying(50)
);


ALTER TABLE public.participant OWNER TO postgres;

--
-- Name: slack; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.slack (
    id integer NOT NULL,
    receiver character varying(50),
    sender character varying(50) NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    task_id character varying(50),
    content text
);


ALTER TABLE public.slack OWNER TO postgres;

--
-- Name: task; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.task (
    id integer NOT NULL,
    task_id bigint
);


ALTER TABLE public.task OWNER TO postgres;

--
-- Name: description id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.description ALTER COLUMN id SET DEFAULT nextval('public.description_id_seq'::regclass);


--
-- Data for Name: description; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.description (id, task_id, content, embedding) FROM stdin;
\.


--
-- Data for Name: employee; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.employee (id, name) FROM stdin;
\.


--
-- Data for Name: notion; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.notion (id, task_id, "timestamp", participant_id, content) FROM stdin;
\.


--
-- Data for Name: onedrive; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.onedrive (id, task_id, "timestamp", writer, content) FROM stdin;
\.


--
-- Data for Name: outlook; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.outlook (id, receiver, sender, "timestamp", task_id, content) FROM stdin;
\.


--
-- Data for Name: participant; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.participant (id, notion_id, p1, p2, p3, p4, p5, p6) FROM stdin;
\.


--
-- Data for Name: slack; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.slack (id, receiver, sender, "timestamp", task_id, content) FROM stdin;
\.


--
-- Data for Name: task; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.task (id, task_id) FROM stdin;
\.


--
-- Name: description_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.description_id_seq', 1, false);


--
-- Name: description description_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.description
    ADD CONSTRAINT description_pkey PRIMARY KEY (id);


--
-- Name: employee employee_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employee
    ADD CONSTRAINT employee_pkey PRIMARY KEY (id);


--
-- Name: notion notion_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notion
    ADD CONSTRAINT notion_pkey PRIMARY KEY (id);


--
-- Name: onedrive onedrive_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.onedrive
    ADD CONSTRAINT onedrive_pkey PRIMARY KEY (id);


--
-- Name: outlook outlook_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.outlook
    ADD CONSTRAINT outlook_pkey PRIMARY KEY (id);


--
-- Name: participant participant_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.participant
    ADD CONSTRAINT participant_pkey PRIMARY KEY (id);


--
-- Name: slack slack_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.slack
    ADD CONSTRAINT slack_pkey PRIMARY KEY (id);


--
-- Name: task task_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task
    ADD CONSTRAINT task_pkey PRIMARY KEY (id);


--
-- PostgreSQL database dump complete
--

\unrestrict aJKSm9umxmErXONQStTRINbCASV5jIuWYHIjEAaHF4b6gL6G1pG2UIa29SVO3DR

