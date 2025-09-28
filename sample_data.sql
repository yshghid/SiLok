--
-- PostgreSQL database dump
--

\restrict 1im2ABbn6N6XxgZGfLymCsfnbTHnKF0ttKxV1uM0hqZz4yKSRI0b9dfobYeQAgh

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
-- Name: project; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA project;


ALTER SCHEMA project OWNER TO postgres;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: postgres
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO postgres;

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
  zero_vec := array_fill(0.0::float, ARRAY[384])::vector;
  norm := NEW.embedding_vector <-> zero_vec;
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
-- Name: administer; Type: TABLE; Schema: project; Owner: postgres
--

CREATE TABLE project.administer (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    email character varying(100) NOT NULL,
    password character varying(255) NOT NULL,
    job_grade character varying(50) NOT NULL,
    task_involved integer[]
);


ALTER TABLE project.administer OWNER TO postgres;

--
-- Name: employee; Type: TABLE; Schema: project; Owner: postgres
--

CREATE TABLE project.employee (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    email character varying(100) NOT NULL,
    password character varying(255) NOT NULL,
    job_grade character varying(50)
);


ALTER TABLE project.employee OWNER TO postgres;

--
-- Name: notion; Type: TABLE; Schema: project; Owner: postgres
--

CREATE TABLE project.notion (
    id integer NOT NULL,
    task_id integer,
    "timestamp" timestamp without time zone NOT NULL,
    participant_id character varying(50),
    content text,
    embedding public.vector(768)
);


ALTER TABLE project.notion OWNER TO postgres;

--
-- Name: onedrive; Type: TABLE; Schema: project; Owner: postgres
--

CREATE TABLE project.onedrive (
    id integer NOT NULL,
    task_id integer,
    "timestamp" timestamp without time zone NOT NULL,
    writer character varying(50),
    content text,
    embedding public.vector(768)
);


ALTER TABLE project.onedrive OWNER TO postgres;

--
-- Name: outlook; Type: TABLE; Schema: project; Owner: postgres
--

CREATE TABLE project.outlook (
    id integer NOT NULL,
    receiver character varying(50),
    sender character varying(50) NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    task_id integer,
    content text,
    embedding public.vector(768)
);


ALTER TABLE project.outlook OWNER TO postgres;

--
-- Name: participant; Type: TABLE; Schema: project; Owner: postgres
--

CREATE TABLE project.participant (
    id integer NOT NULL,
    notion_id integer,
    p1 character varying(50),
    p2 character varying(50),
    p3 character varying(50),
    p4 character varying(50),
    p5 character varying(50),
    p6 character varying(50)
);


ALTER TABLE project.participant OWNER TO postgres;

--
-- Name: report; Type: TABLE; Schema: project; Owner: postgres
--

CREATE TABLE project.report (
    id integer NOT NULL,
    task_id integer,
    "timestamp" timestamp without time zone NOT NULL,
    writer character varying(50),
    email character varying(100),
    report text,
    report_embedded public.vector(384)
);


ALTER TABLE project.report OWNER TO postgres;

--
-- Name: slack; Type: TABLE; Schema: project; Owner: postgres
--

CREATE TABLE project.slack (
    id integer NOT NULL,
    receiver character varying(50),
    sender character varying(50) NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    task_id integer,
    content text,
    embedding public.vector(768)
);


ALTER TABLE project.slack OWNER TO postgres;

--
-- Name: task; Type: TABLE; Schema: project; Owner: postgres
--

CREATE TABLE project.task (
    id integer NOT NULL,
    task_uuid character varying(50),
    description text
);


ALTER TABLE project.task OWNER TO postgres;

--
-- Name: administer_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.administer_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.administer_id_seq OWNER TO postgres;

--
-- Name: administer; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.administer (
    id integer DEFAULT nextval('public.administer_id_seq'::regclass) NOT NULL,
    name character varying(50) NOT NULL,
    email character varying(100) NOT NULL,
    password character varying(255) NOT NULL,
    job_grade character varying(50) NOT NULL,
    task_involved integer[]
);


ALTER TABLE public.administer OWNER TO postgres;

--
-- Name: employee_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.employee_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.employee_id_seq OWNER TO postgres;

--
-- Name: employee; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.employee (
    id integer DEFAULT nextval('public.employee_id_seq'::regclass) NOT NULL,
    name character varying(50) NOT NULL,
    email character varying(100) NOT NULL,
    password character varying(255) NOT NULL,
    job_grade character varying(50)
);


ALTER TABLE public.employee OWNER TO postgres;

--
-- Name: notion_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.notion_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.notion_id_seq OWNER TO postgres;

--
-- Name: notion; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.notion (
    id integer DEFAULT nextval('public.notion_id_seq'::regclass) NOT NULL,
    task_id integer,
    "timestamp" timestamp without time zone NOT NULL,
    participant_id character varying(50),
    content text,
    embedding public.vector(768)
);


ALTER TABLE public.notion OWNER TO postgres;

--
-- Name: onedrive_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.onedrive_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.onedrive_id_seq OWNER TO postgres;

--
-- Name: onedrive; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.onedrive (
    id integer DEFAULT nextval('public.onedrive_id_seq'::regclass) NOT NULL,
    task_id integer,
    "timestamp" timestamp without time zone NOT NULL,
    writer character varying(50),
    content text,
    embedding public.vector(768)
);


ALTER TABLE public.onedrive OWNER TO postgres;

--
-- Name: outlook_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.outlook_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.outlook_id_seq OWNER TO postgres;

--
-- Name: outlook; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.outlook (
    id integer DEFAULT nextval('public.outlook_id_seq'::regclass) NOT NULL,
    receiver character varying(50),
    sender character varying(50) NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    task_id integer,
    content text,
    embedding public.vector(768)
);


ALTER TABLE public.outlook OWNER TO postgres;

--
-- Name: participant_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.participant_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.participant_id_seq OWNER TO postgres;

--
-- Name: participant; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.participant (
    id integer DEFAULT nextval('public.participant_id_seq'::regclass) NOT NULL,
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
-- Name: report_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.report_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.report_id_seq OWNER TO postgres;

--
-- Name: report; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.report (
    id integer DEFAULT nextval('public.report_id_seq'::regclass) NOT NULL,
    task_id integer,
    "timestamp" timestamp without time zone NOT NULL,
    writer character varying(50),
    email character varying(100),
    report text,
    report_embedded public.vector(384)
);


ALTER TABLE public.report OWNER TO postgres;

--
-- Name: slack_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.slack_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.slack_id_seq OWNER TO postgres;

--
-- Name: slack; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.slack (
    id integer DEFAULT nextval('public.slack_id_seq'::regclass) NOT NULL,
    receiver character varying(50),
    sender character varying(50) NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    task_id integer,
    content text,
    embedding public.vector(768)
);


ALTER TABLE public.slack OWNER TO postgres;

--
-- Name: task_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.task_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.task_id_seq OWNER TO postgres;

--
-- Name: task; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.task (
    id integer DEFAULT nextval('public.task_id_seq'::regclass) NOT NULL,
    task_uuid character varying(50),
    description text
);


ALTER TABLE public.task OWNER TO postgres;

--
-- Data for Name: administer; Type: TABLE DATA; Schema: project; Owner: postgres
--

COPY project.administer (id, name, email, password, job_grade, task_involved) FROM stdin;
\.


--
-- Data for Name: employee; Type: TABLE DATA; Schema: project; Owner: postgres
--

COPY project.employee (id, name, email, password, job_grade) FROM stdin;
\.


--
-- Data for Name: notion; Type: TABLE DATA; Schema: project; Owner: postgres
--

COPY project.notion (id, task_id, "timestamp", participant_id, content, embedding) FROM stdin;
\.


--
-- Data for Name: onedrive; Type: TABLE DATA; Schema: project; Owner: postgres
--

COPY project.onedrive (id, task_id, "timestamp", writer, content, embedding) FROM stdin;
\.


--
-- Data for Name: outlook; Type: TABLE DATA; Schema: project; Owner: postgres
--

COPY project.outlook (id, receiver, sender, "timestamp", task_id, content, embedding) FROM stdin;
\.


--
-- Data for Name: participant; Type: TABLE DATA; Schema: project; Owner: postgres
--

COPY project.participant (id, notion_id, p1, p2, p3, p4, p5, p6) FROM stdin;
\.


--
-- Data for Name: report; Type: TABLE DATA; Schema: project; Owner: postgres
--

COPY project.report (id, task_id, "timestamp", writer, email, report, report_embedded) FROM stdin;
\.


--
-- Data for Name: slack; Type: TABLE DATA; Schema: project; Owner: postgres
--

COPY project.slack (id, receiver, sender, "timestamp", task_id, content, embedding) FROM stdin;
\.


--
-- Data for Name: task; Type: TABLE DATA; Schema: project; Owner: postgres
--

COPY project.task (id, task_uuid, description) FROM stdin;
\.


--
-- Data for Name: administer; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.administer (id, name, email, password, job_grade, task_involved) FROM stdin;
1	김민준	kimminjun@skax.co.kr	1111	관리자	{1,2}
2	박서연	parkseoyeon@skax.co.kr	2222	관리자	{1,2}
3	이수진	leesujin@skax.co.kr	3333	관리자	{1,2}
4	최준영	choijunyoung@skax.co.kr	4444	관리자	{1,2}
\.


--
-- Data for Name: employee; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.employee (id, name, email, password, job_grade) FROM stdin;
1	서은수	eunsuseo@skax.co.kr	1111	매니저
2	윤소현	shyoun@skax.co.kr	2222	매니저
3	박현규	bakhg@skax.co.kr	3333	매니저
4	정도현	dohyunj@skax.co.kr	4444	매니저
5	박범준	parkbj@skax.co.kr	5555	매니저
6	조성호	choseongho@skax.co.kr	6666	매니저
\.


--
-- Data for Name: notion; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.notion (id, task_id, "timestamp", participant_id, content, embedding) FROM stdin;
1	1	2025-09-23 10:00:00	1	이번 주 온라인 쇼핑몰 시스템 구축 관련 회의 내용 정리/n...	\N
2	2	2025-09-23 10:00:00	2	이번 주 병원 예약·진료 시스템 통합 회의 노트입니다./n...	\N
\.


--
-- Data for Name: onedrive; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.onedrive (id, task_id, "timestamp", writer, content, embedding) FROM stdin;
1	1	2025-09-24 17:15:00	윤소현	결제 모듈 안정화 테스트 결과 보고서/n...	\N
2	2	2025-09-24 16:00:00	박범준	환자 예약 데이터/n...	\N
\.


--
-- Data for Name: outlook; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.outlook (id, receiver, sender, "timestamp", task_id, content, embedding) FROM stdin;
1	윤소현	서은수	2025-09-23 08:30:00	1	안녕하세요/n이번 주 온라인 쇼핑몰 결제 모듈 점검 회의...	\N
2	서은수	윤소현	2025-09-24 17:20:00	1	안녕하세요/n이번 주 테스트 결과 정리 문서...	\N
3	박범준	박현규	2025-09-23 14:00:00	2	안녕하세요/n이번 주 병원 예약·진료 시스템 통합 관련 회의...	\N
4	박현규	박범준	2025-09-24 16:30:00	2	안녕하세요/n이번 주 작업 중간 결과를 정리한 파일...	\N
\.


--
-- Data for Name: participant; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.participant (id, notion_id, p1, p2, p3, p4, p5, p6) FROM stdin;
1	1	서은수	윤소현	\N	\N	\N	\N
2	2	박현규	박범준	\N	\N	\N	\N
\.


--
-- Data for Name: report; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.report (id, task_id, "timestamp", writer, email, report, report_embedded) FROM stdin;
1	1	2025-09-27 14:29:09.204511	서은수	eunsuseo@skax.co.kr	# 업무 1: 온라인 쇼핑몰 시스템 구축 주간 보고서\n\n## 1) 주간 요약\n이번 주에는 온라인 쇼핑몰 시스템 구축 관련하여 여러 가지 진행 상황이 있었습니다. 결제 모듈 안정화 테스트가 순조롭게 진행되었으며, 결제 모듈의 속도가 평균 0.8초로 개선되었습니다. 그러나 서버 응답 지연 문제가 발생하여 이를 해결하기 위한 모니터링 강화와 서버 자원 부족 문제 해결이 필요합니다. 상품 검색 속도는 DB 인덱스 조정으로 약 20% 개선되었습니다. 캐시 서버 적용은 다음 주에 PoC 시작이 가능할 것으로 보입니다. H카드사와의 결제 모듈 연동 테스트에서 오류가 발생하여 추가적인 협의가 필요합니다.\n\n## 2) 사람별 주요 산출물\n- **윤소현**: 결제 모듈 안정화 테스트 로그 업로드 및 결과 요약 정리, 임원 보고 자료 준비.\n- **서은수**: DB 인덱스 조정 및 검색 속도 개선, 서버 모니터링 강화 및 응답 지연 문제 해결 방안 마련.\n\n## 3) 협업 내역\n- **Slack**: 실시간 커뮤니케이션을 통해 결제 모듈 테스트 진행 상황 및 서버 지연 문제 논의.\n- **Notion**: 프로젝트 진행 상황 및 보고서 초안 작성.\n- **Outlook**: SK 회사와의 회의 일정 조율 및 임원 보고 자료 공유.\n- **OneDrive**: 결제 모듈 테스트 로그 및 보고서 자료 업로드 및 공유.\n\n## 4) 리스크/이슈\n- **서버 응답 지연 문제**: 동시 접속자 증가로 인한 서버 자원 부족 문제로 CPU 사용률이 높아지는 현상 발생.\n- **결제 모듈 연동 오류**: H카드사와의 연동 테스트에서 오류 발생, SK 회사와의 협의 필요.\n\n## 5) 차주 계획\n- **서버 자원 확충 및 모니터링 강화**: 서버 응답 지연 문제 해결을 위한 자원 확충 및 모니터링 시스템 강화.\n- **캐시 서버 PoC 시작**: SK 회사 클라우드 자원 할당 확정 후 캐시 서버 PoC 진행.\n- **H카드사 연동 오류 해결**: H카드사와의 협의를 통해 연동 오류 해결 방안 마련.\n- **최종 보고서 작성 및 제출**: 이번 주 보고서 최종 버전 마무리 및 제출.	[0.0307829,0.02844913,0.048450552,0.019198952,-0.0069316844,-0.063641675,-0.008259667,0.06856789,-0.02219482,-0.059764147,0.10327238,0.010525808,0.09294446,-0.009726733,0.041741103,-0.057567004,0.016172018,0.053473826,-0.052216392,0.060233567,0.06851062,-0.052700624,-0.017700925,-0.009629967,-0.088916644,0.005673435,-0.06665366,0.049490195,-0.030116525,0.0744926,-0.023780514,0.013131513,-0.0334198,-0.054973345,-0.115565106,0.0006504491,0.010524713,0.027627641,-0.06974445,0.016226066,-0.05732029,-0.09470145,0.00822924,-0.09291084,-0.00534619,0.044293806,-0.035760004,-0.07956917,-0.10990665,-0.04480705,-0.0017609406,0.0011929288,0.005708708,-0.02823389,-0.023564162,-0.07346421,-0.071011014,0.04260527,-0.005810056,0.082741775,-0.06916239,0.03613322,0.00498099,-0.00428871,0.091435425,-0.04341421,-0.005401521,-0.080267675,0.00543249,0.06925895,0.0708779,-0.007180583,0.015501461,-0.06199078,-0.071040645,-0.056107722,-0.012296682,0.014282387,-0.07968221,-0.06866605,0.051037684,-0.059610035,-0.008367682,-0.04632841,-0.066172354,-0.009909332,-0.053901963,-0.034330282,-0.02882882,0.06127736,0.11145296,0.16418518,0.043067023,-0.031662103,0.04907231,0.012640229,-0.108009785,0.09016607,0.0102737425,-0.035093267,-0.0059923804,-0.009051122,-0.09502026,-0.025915045,0.0017974616,0.049377885,-0.025763279,-0.047728207,0.009677341,-0.009517941,-0.024278527,0.0060810633,-0.037304707,0.0066204355,-0.059141997,0.009270243,-0.026930194,-0.018725106,-0.010211571,0.02919044,0.03630431,-0.10563078,0.11556599,-0.039146967,0.0025507468,-0.11307426,0.013089602,-2.8979958e-34,-0.057628613,-0.07175124,-0.0046956344,-0.03378199,0.022896178,0.0490433,-0.019265445,-0.031850696,0.08270259,-0.008628889,0.0010733968,1.358525e-05,-0.031595092,0.0188829,-0.016429247,0.05327289,0.022929667,0.021302065,-0.08508288,0.037140835,0.054522023,-0.012007297,0.028075332,0.049596395,0.01136742,0.012178664,0.058673147,-0.015541152,-0.06775042,0.0014920068,0.005175255,-0.039403424,-0.06716755,-0.025494933,-0.089933746,0.054132696,0.048732314,-0.01963175,-0.042468026,-0.04217071,-0.032916564,0.02647613,0.04536122,0.058347322,0.011149328,0.029792758,-0.055068217,0.016306732,-0.06051173,-0.0054076007,-0.089031026,0.06399942,0.011953068,-0.049664855,0.041555926,0.09871752,0.076707296,0.0032230115,-0.05206141,-0.017006882,-0.069792,0.0856843,-0.044453066,-0.027521964,0.04794641,0.031387534,0.037541967,7.2594936e-05,-0.04502696,-0.02527427,0.01635218,-0.034060173,-0.11003913,0.047146574,0.012256457,-0.07392797,-0.054731276,0.03478359,0.009878927,-0.013141929,0.01871276,0.004022051,-0.030784566,-0.046058368,0.036935184,0.0919912,0.013981053,-0.045028318,0.033979952,0.09769347,0.015001061,0.015219097,0.033584014,-0.03714715,0.032298338,-5.1536714e-33,-0.024967609,0.14428248,-0.030383332,0.057573125,0.07491522,0.06779266,-0.034827627,-0.024958093,0.001452719,0.027250476,-0.04018696,0.046544563,0.0006940526,-0.02408796,-0.0018157047,0.008606926,0.010791289,0.013846965,-0.0847923,0.02518547,0.06946724,0.016242823,0.059044186,0.053884257,-0.09984485,-0.0605729,-0.0037957518,0.026367676,-0.040869236,-0.0014299834,0.08284441,0.06476832,-0.00043574645,0.020327894,0.035680797,-0.008295523,-0.036090724,0.020717967,-0.03711935,-0.09581671,0.05452495,-0.01958911,0.11881402,-0.08141238,-0.04923218,-0.030686557,0.0027266017,-0.073825546,-0.006770141,-0.022589346,0.031336192,0.05269016,-0.10541237,-0.05855407,0.070095085,-0.011600271,0.08324895,-0.055608682,-0.10677524,-0.06860924,0.032044735,0.035180602,-0.035672218,-0.019859433,-0.03879181,0.034895916,0.05313271,0.030819017,0.05274768,-0.056288302,-0.0225264,-0.043146208,0.04292773,-0.003045282,-0.0360656,0.004464642,0.02851478,0.062808216,-0.0005511323,-0.01678124,-0.14678603,0.039686315,-0.018001102,-0.029941386,-0.060150992,-0.036332592,-0.011482994,-0.07139903,0.039138474,-0.067568704,0.023827182,0.045564823,0.017825505,-0.045279846,0.031214481,-3.8226073e-08,-0.0021396189,-0.006281958,0.050374858,0.030863343,-0.06567211,0.013635145,-0.024056677,0.015350585,-0.05421994,-0.015351398,-0.007975409,0.040219333,0.08238939,0.033556968,-0.08893763,-0.09488374,0.06546097,-0.009863511,-0.0019262474,0.06870116,0.07043277,-0.036286894,-0.023201477,0.05543834,-0.055424854,0.036351454,-0.018732565,-0.00057661807,-0.09260124,0.028624319,-0.018597262,-0.045832824,-0.010747501,0.028403644,0.055158574,-0.10237911,0.013958308,0.030719055,-0.0149304755,0.11731819,0.0055189407,-0.112124525,0.08093201,0.12068646,0.017234778,-0.06952352,0.022086123,-0.059916954,-0.019450322,0.07744477,-0.009455339,-0.043242607,0.0034048103,-0.028014012,-0.026198376,0.010985461,-0.0013735695,0.0020068784,-0.00760964,0.019178577,0.01492297,-0.025535317,-0.042172417,0.019216238]
2	1	2025-09-27 14:29:27.102751	서은수	eunsuseo@skax.co.kr	# 업무 1: 온라인 쇼핑몰 시스템 구축 주간 보고서\n\n## 1) 주간 요약\n\n이번 주에는 온라인 쇼핑몰 시스템 구축 관련하여 여러 가지 중요한 작업이 진행되었습니다. 결제 모듈의 안정화 테스트가 성공적으로 진행되었으며, 결제 모듈의 속도가 평균 0.8초로 개선되었습니다. 그러나 서버 응답 지연 문제가 발생하여 원인을 분석한 결과, 동시 접속자 증가로 인한 CPU 사용률 급증이 원인으로 파악되었습니다. 이를 해결하기 위해 서버 모니터링을 강화하고, DB 인덱스 조정을 통해 상품 검색 속도를 약 20% 개선하였습니다. 캐시 서버 적용은 다음 주에 PoC를 시작할 예정입니다. 임원 보고 준비도 완료되었으며, 결제 모듈 개선 사항과 서버 응답 지연 이슈를 포함한 보고 자료가 준비되었습니다.\n\n## 2) 사람별 주요 산출물\n\n- **윤소현**: 결제 모듈 안정화 테스트 로그 업로드 및 보고 자료 정리, 서버 응답 지연 원인 분석.\n- **서은수**: DB 인덱스 조정 및 검색 속도 개선, 캐시 서버 적용 계획 수립.\n\n## 3) 협업 내역\n\n- Slack을 통해 결제 모듈 속도 개선 및 서버 지연 문제에 대한 실시간 커뮤니케이션.\n- Notion을 활용하여 프로젝트 진행 상황 및 보고서 작성 협업.\n- Outlook을 통해 SK 회사와의 회의 일정 조율 및 임원 보고 준비.\n- OneDrive에 테스트 로그 및 보고 자료 업로드 및 공유.\n\n## 4) 리스크/이슈\n\n- **서버 응답 지연 문제**: 동시 접속자 증가로 인한 CPU 사용률 급증이 문제로 파악됨. 서버 자원 부족 문제 해결 필요.\n- **카드사 연동 오류**: H카드사와의 연동 테스트 중 오류 발생. SK 회사와 협의 필요.\n\n## 5) 차주 계획\n\n- 서버 자원 확충 및 모니터링 시스템 강화.\n- H카드사 연동 오류 해결 및 추가 테스트 진행.\n- 캐시 서버 PoC 시작 및 성능 평가.\n- 임원 보고서 피드백 반영 및 최종 보고서 제출.	[0.034476887,0.0179603,0.054394186,0.022296434,-0.024077795,-0.06602021,-0.0033365705,0.06847162,-0.018299777,-0.056775372,0.098063186,0.0054703816,0.090290986,-0.009749676,0.04263424,-0.058139555,0.024457535,0.046510957,-0.06047145,0.060390208,0.07003444,-0.048298202,-0.013235095,-0.0010692469,-0.09194654,-0.002379061,-0.06002563,0.037298854,-0.029584035,0.074641,-0.018751511,0.026702711,-0.029996453,-0.062743284,-0.11058167,0.009107867,0.005203552,0.032301363,-0.07377482,0.016394814,-0.06288851,-0.0929452,0.015990302,-0.10184337,-0.007374013,0.04620436,-0.04413892,-0.085428625,-0.106901444,-0.03700686,-0.005692173,-0.0029489333,0.007070838,-0.030348456,-0.032921243,-0.07956713,-0.072772615,0.040442612,-0.0159515,0.09071158,-0.067830816,0.03786998,0.012704559,0.0010118494,0.09971904,-0.03607368,-6.0700175e-05,-0.083010904,0.0039432514,0.059215818,0.07784795,0.00024004014,0.014621842,-0.054641906,-0.0750598,-0.05711062,-0.019731838,0.010307951,-0.07991664,-0.06126203,0.04717692,-0.05481357,-0.011822241,-0.042209394,-0.075977765,-0.018171132,-0.054422393,-0.037177034,-0.039731253,0.06596599,0.11412635,0.15768409,0.0199343,-0.039259598,0.05257253,0.015319817,-0.109715104,0.09101446,0.012495957,-0.039950978,-0.004911238,-0.008592794,-0.08136039,-0.017820828,0.004968755,0.043986246,-0.0051017627,-0.05138361,0.006231166,-0.0094024995,-0.028800482,0.0071089664,-0.044769537,0.008728587,-0.05894266,0.011167272,-0.028153196,-0.015094185,-0.00644731,0.03193099,0.030755898,-0.1161304,0.11444675,-0.040511847,0.0010833892,-0.10983653,0.013222675,7.925559e-34,-0.056677137,-0.07407844,0.007850292,-0.025740378,0.0319626,0.053344794,-0.01734257,-0.04059293,0.08768665,-0.010211689,-0.005470135,0.0058458056,-0.022921091,0.011154633,-0.008207293,0.04639991,0.016339475,0.0255084,-0.08953942,0.038718723,0.052627992,-0.0067272843,0.020982856,0.049739663,0.011096354,0.010431363,0.056706715,-0.0058627734,-0.08274189,-0.0003238611,0.00953761,-0.025437841,-0.057761345,-0.036903344,-0.08782889,0.048583757,0.052174818,-0.013242737,-0.03173782,-0.047845516,-0.031030513,0.02398421,0.046991374,0.0634716,0.0061843926,0.035909347,-0.055028662,0.0058716447,-0.055288684,-0.0033911394,-0.08479773,0.06373988,0.015216946,-0.05795201,0.049928263,0.0911609,0.068801604,0.0033628792,-0.058263645,-0.012820374,-0.05990018,0.08555255,-0.04806482,-0.036769673,0.04965386,0.032869,0.02910596,-0.0025470702,-0.038897138,-0.013312405,0.017772939,-0.032000285,-0.09812639,0.055712476,0.010556268,-0.0645359,-0.06700683,0.026348865,-0.0015136745,-0.0042358455,0.018810812,0.0033300833,-0.027008494,-0.05160446,0.04273873,0.098420314,0.0054973243,-0.0367086,0.03935321,0.09441359,0.02518923,0.018356482,0.026493702,-0.0329696,0.024888828,-6.0489665e-33,-0.02160983,0.14967906,-0.026542863,0.05372306,0.087637216,0.07059202,-0.03028157,-0.019082377,0.010819802,0.030141821,-0.041236974,0.053114276,-0.007153617,-0.033881556,-0.0045065754,0.013472831,0.007076682,0.013742559,-0.07496917,0.02378943,0.062353753,0.034085564,0.05841042,0.05153207,-0.09845045,-0.056550708,-0.016931003,0.021157464,-0.047644995,-0.0016799328,0.07482191,0.056999467,0.0061105904,0.013869595,0.04007342,-0.02733252,-0.03807159,0.015177726,-0.037487093,-0.09632764,0.051573776,-0.02693228,0.12636255,-0.09275058,-0.039337743,-0.027988987,0.004810404,-0.07697365,-0.010672593,-0.02416953,0.029668316,0.04557467,-0.10340082,-0.048029363,0.07487513,-0.02689355,0.072626814,-0.060075045,-0.100270934,-0.061597053,0.03671121,0.028111842,-0.032582283,-0.01336795,-0.044171873,0.04331923,0.04767253,0.031131733,0.04781735,-0.04538339,-0.030888628,-0.058074523,0.04295961,-0.004334536,-0.043353017,0.008470408,0.021512588,0.0550343,-0.008638195,-0.013278008,-0.14431174,0.03797052,-0.028843861,-0.027430892,-0.07108294,-0.032128815,-0.013433142,-0.0723866,0.027592614,-0.056335207,0.015953626,0.039616004,0.017842427,-0.043331947,0.035813645,-4.3123144e-08,0.0015698791,-0.023990907,0.053570513,0.031365123,-0.06328711,0.0040681376,-0.023732128,0.014407877,-0.052217696,-0.0076422556,-0.010652439,0.043111317,0.08033075,0.03440686,-0.08165784,-0.09601798,0.06283277,-0.0060049132,-0.0023739755,0.057001173,0.074353345,-0.045398507,-0.016468637,0.039852697,-0.054715622,0.04369758,-0.013579105,0.0025444878,-0.09496672,0.027307793,-0.01488458,-0.048696566,-0.00050951046,0.02593896,0.053815108,-0.109214574,0.015954813,0.03311159,-0.019851997,0.12745544,-0.00086271105,-0.11041093,0.08556443,0.123423785,0.024842631,-0.07401382,0.028858343,-0.052612573,-0.01140206,0.081585534,-0.0071024257,-0.032418787,-0.005020324,-0.030966451,-0.028223347,0.013848707,-0.004384017,0.008216458,-0.003407301,0.015614377,0.021714384,-0.013577694,-0.041036278,0.013454063]
3	1	2025-09-27 14:29:43.070183	서은수	eunsuseo@skax.co.kr	# 업무 1: 온라인 쇼핑몰 시스템 구축 주간 보고서\n\n## 1) 주간 요약\n이번 주 온라인 쇼핑몰 시스템 구축 프로젝트의 주요 진행 상황은 다음과 같습니다:\n\n- **결제 모듈 안정화 테스트**: 결제 모듈의 속도가 평균 0.8초로 개선되었습니다. 그러나 서버 응답 지연 문제가 발생하여 원인을 조사한 결과, 동시 접속자 증가로 인한 CPU 사용률 급증(최대 95%)이 원인임을 확인했습니다. 이에 대한 모니터링을 강화하고 있습니다.\n\n- **검색 속도 개선**: DB 인덱스 조정을 통해 상품 검색 속도가 약 20% 개선되었습니다. 캐시 서버 적용은 다음 주에 PoC를 시작할 예정이며, SK 회사의 클라우드 자원 할당이 확정되면 진행할 수 있습니다.\n\n- **서버 지연 문제**: 서버 지연 문제는 여전히 개선이 필요하며, 특히 오후 8시경에 발생할 가능성이 높아 모니터링을 강화하고 있습니다.\n\n- **임원 보고 준비**: SK 회사 임원 보고를 위해 회의실을 예약하고, 보고 자료를 준비했습니다. 결제 모듈 개선 사항과 서버 응답 지연 이슈를 정리하여 발표했습니다.\n\n- **카드사 연동 테스트**: 결제 모듈 카드사 연동 테스트 중 H카드사에서 오류가 발생하여 에러 로그를 정리 중입니다.\n\n## 2) 사람별 주요 산출물\n- **윤소현**: 결제 모듈 안정화 테스트 로그 업로드 및 결과 요약 정리.\n- **서은수**: DB 최적화 결과 및 캐시 서버 적용 계획 정리, 임원 보고 자료 준비.\n\n## 3) 협업 내역\n- **Slack/Notion/Outlook/OneDrive**를 통해 팀원 간의 원활한 커뮤니케이션과 자료 공유가 이루어졌습니다. 특히, 결제 모듈 테스트 결과와 서버 지연 문제에 대한 논의가 활발히 진행되었습니다.\n\n## 4) 리스크/이슈\n- **서버 응답 지연 문제**: 동시 접속자 증가로 인한 서버 자원 부족이 문제로, 이를 해결하기 위한 모니터링 강화 및 서버 자원 확충이 필요합니다.\n- **카드사 연동 오류**: H카드사와의 연동 오류가 발생하여, SK 회사와의 협의가 필요할 수 있습니다.\n\n## 5) 차주 계획\n- **캐시 서버 PoC 시작**: SK 회사의 클라우드 자원 할당이 확정되면 캐시 서버 PoC를 시작합니다.\n- **서버 자원 확충 방안 마련**: 서버 응답 지연 문제를 해결하기 위한 자원 확충 방안을 마련합니다.\n- **카드사 연동 오류 해결**: H카드사와의 연동 오류를 해결하기 위한 협의를 진행합니다.\n- **결제 모듈 및 검색 기능 개선 지속**: 결제 모듈과 검색 기능의 지속적인 개선을 위해 추가적인 테스트와 최적화를 진행합니다.	[0.032988105,0.031190883,0.0473385,0.031345814,-0.0072064013,-0.058144514,-0.024284808,0.078860104,-0.01792879,-0.04809909,0.11193423,-0.004458471,0.07231223,-0.016110813,0.052355047,-0.048321832,0.005269486,0.037387107,-0.04565736,0.06837422,0.052721813,-0.053337988,-0.0031659498,-0.0065020933,-0.086650744,0.0028943429,-0.04708508,0.03345836,-0.015519782,0.08406275,-0.024502797,0.044485457,-0.014824367,-0.062306635,-0.10911953,0.013000138,0.010631985,0.046362616,-0.076652,0.014578007,-0.06665463,-0.07529702,0.015203757,-0.114408,-0.030126734,0.031123241,-0.03985474,-0.09354331,-0.1263965,-0.02560056,-0.014235584,-0.012555297,0.017671429,-0.035880096,-0.033410102,-0.07360654,-0.08267074,0.043300904,-0.0069362526,0.06585706,-0.07663211,0.031858344,-0.013196422,-0.0049996963,0.09255021,-0.013844602,0.0029981264,-0.07554959,0.023150044,0.07521265,0.074098535,-0.018041156,0.020787345,-0.042453665,-0.08309833,-0.047873218,-0.0047446187,0.016049763,-0.07276644,-0.06977251,0.08248326,-0.031711057,-0.014145105,-0.04823967,-0.087323256,-0.010723801,-0.056768104,-0.040500313,-0.03635823,0.05434482,0.109315105,0.13595767,0.009692031,-0.06741146,0.046931352,0.00915425,-0.09809905,0.08135246,0.029487232,-0.024220986,-0.0015475836,0.0008804855,-0.079238385,-0.03134642,-0.007087238,0.03211823,-0.009751316,-0.043663613,0.006876751,-0.004990156,-0.05853679,0.0020343445,-0.041536167,0.011111515,-0.014636627,0.0007112801,-0.020230403,-0.025165677,0.0061022993,0.035166673,0.056676596,-0.122049615,0.11838509,-0.035267204,0.007360571,-0.09639108,0.0049647707,-1.0985579e-34,-0.0518256,-0.06994581,-0.013370625,-0.029547319,0.013403542,0.052501284,-0.0075629232,-0.040893722,0.08339395,-0.013482561,-0.0076901973,0.0077438047,-0.022273239,0.016246805,-0.0067867963,0.049280927,0.0049005877,0.022620877,-0.08321627,0.025630858,0.047618076,-0.0068015503,0.024166973,0.042510446,0.0024503272,-0.014785939,0.06022807,-0.018380607,-0.07591628,-0.010363518,0.013065487,-0.040802613,-0.05917062,-0.050953925,-0.07303399,0.05130656,0.0680788,-0.017290141,-0.022200784,-0.054640602,-0.0325788,0.025678953,0.033226527,0.06472004,0.015152867,0.06570869,-0.050619856,-0.011709377,-0.052718982,0.009943378,-0.092318304,0.051119205,0.012580482,-0.074908406,0.024105748,0.08061863,0.05686434,-0.0026971211,-0.055783276,-0.010174129,-0.044945493,0.09636368,-0.055995796,-0.04454549,0.052735284,0.031873368,0.014655642,-0.012355234,-0.048895698,-0.008023367,0.0018757042,-0.036312606,-0.12015532,0.053064954,0.03463224,-0.0815331,-0.06413047,0.03437709,0.00062519545,0.003481865,0.016819647,-0.008073784,-0.012591187,-0.05720677,0.046744738,0.08848715,0.020204337,-0.050554756,0.044150162,0.101740435,0.014612711,0.016304368,0.01901816,-0.015171994,0.02583067,-5.83905e-33,-0.02056524,0.13321301,-0.015897684,0.0617133,0.061642192,0.07967527,-0.045844898,-0.0028790745,0.009734473,0.01337851,-0.021821937,0.071087554,-0.0014007342,-0.041243833,-0.0012283132,-0.0032475828,0.008580852,0.022228647,-0.07709128,0.019225094,0.045616142,0.045450047,0.051462065,0.034789238,-0.09711226,-0.06401125,-0.0027589798,0.013140788,-0.02568304,0.0120295305,0.087497644,0.06864991,0.011513911,0.017238514,0.041037656,-0.02436795,-0.028375184,0.0166485,-0.046664648,-0.08775857,0.033348955,-0.0073726173,0.115085945,-0.10973556,-0.019880654,-0.019444488,0.0024746915,-0.07792373,-0.014239467,-0.030526303,0.050648596,0.04427822,-0.10387082,-0.051276017,0.07169152,-0.01897934,0.07998008,-0.07142826,-0.11513639,-0.05358058,0.018973453,0.02722784,-0.046407368,-0.027123913,-0.026841594,0.032076787,0.060341876,0.02571993,0.05572792,-0.04133483,-0.031352602,-0.062459033,0.04796743,-0.002851533,-0.038510866,-0.006034133,-0.0022240104,0.053832263,0.005757717,-0.021661589,-0.13875836,0.042430222,-0.0036432573,-0.041464396,-0.07201017,-0.010839879,-0.029143954,-0.054219805,0.031872645,-0.057624005,0.0063123805,0.014786566,-0.01237584,-0.04059626,0.04314171,-4.56196e-08,0.01359802,-0.028687574,0.064017095,0.037787423,-0.041150022,0.018962214,-0.003283732,0.0131017435,-0.04776098,0.026499126,-0.0196221,0.051506463,0.06673301,0.045227982,-0.09722315,-0.10517551,0.083661735,-0.007036108,-0.0041251704,0.052266486,0.06267366,-0.04237339,-0.010855597,0.029318389,-0.034791514,0.03403899,-0.013865998,0.0061464803,-0.091644935,0.021340802,-0.015785549,-0.038309336,0.0035181467,0.015450542,0.036257517,-0.121247694,0.038588393,0.032804195,-0.02849225,0.13645375,0.0013927545,-0.113905855,0.0875091,0.11916344,0.018166143,-0.08437299,0.039348293,-0.05448814,0.0011499203,0.06202553,-0.016691104,-0.025788695,-0.0041738786,-0.035527308,-0.05443686,0.0046222825,-0.010657383,0.023775747,-0.0160146,-0.018182993,0.061891176,-0.018508025,-0.03626395,0.022377389]
4	2	2025-09-27 14:30:17.489187	박현규	bakhg@skax.co.kr	# 업무 2: 병원 예약·진료 시스템 통합 주간 보고서\n\n## 1) 주간 요약\n이번 주에는 병원 예약·진료 시스템 통합 작업이 진행되었습니다. 주요 작업으로는 모바일 예약 화면의 버튼 크기 조정, 예약 UI 개선, 검사 결과 자동 연동 기능의 DB 샘플 테이블 생성, 병원 예약 UI에 캘린더 추가 등이 있었습니다. 그러나 예약 데이터 중복 저장 문제와 검사 결과 불러오기 속도 저하 등의 이슈가 발생했습니다. 중복 예약 문제는 예약 ID 외에 전화번호를 추가로 체크하는 방식으로 해결을 모색 중입니다. SK헬스케어와의 회의에서는 UI 개선 현황과 DB 중복 이슈 해결 방안이 논의되었습니다.\n\n## 2) 사람별 주요 산출물\n- **박범준**: 모바일 예약 화면 버튼 크기 조정, 예약 UI 개선, 검사 결과 자동 연동 기능 DB 샘플 테이블 생성.\n- **박현규**: 병원 예약 UI에 캘린더 추가, DB 중복 방지 로직 수정, 검사 결과 불러오기 속도 개선 작업.\n\n## 3) 협업 내역\n- **Slack**: 실시간 커뮤니케이션을 통해 UI 개선 및 DB 이슈 논의.\n- **Notion**: 프로젝트 진행 상황 및 회의 준비 자료 정리.\n- **Outlook**: SK헬스케어와의 회의 일정 조율 및 결과 공유.\n- **OneDrive**: hospital_reservation_integration.xlsx 파일 공유 및 피드백.\n\n## 4) 리스크/이슈\n- **예약 데이터 중복 저장 문제**: 같은 환자가 여러 번 시도할 때 발생. 예약 ID 외에 전화번호를 체크하여 해결 방안 모색 중.\n- **검사 결과 불러오기 속도 저하**: DB 인덱스 추가를 통해 조회 속도 개선 예정.\n\n## 5) 차주 계획\n- **중복 예약 방지 로직 점검 및 개선**: 병원 예약 시스템의 핵심 문제로, 철저한 테스트와 수정 필요.\n- **검사 결과 불러오기 속도 개선**: DB 인덱스 추가 및 최적화 작업 진행.\n- **UI 스크린샷 추가 및 문서화**: OneDrive에 공유된 파일에 UI 스크린샷 추가.\n- **SK헬스케어와의 후속 회의 준비**: 개선된 UI 및 DB 구조 수정안 발표 준비.	[0.03445021,0.035352804,0.04032204,-0.0024638923,-0.04144494,-0.061563067,-0.009852807,0.043103945,-0.04602244,-0.04070058,0.09113819,-0.0055042626,0.108242504,-0.06790121,0.03091712,-0.04337818,0.012870539,-0.0042668595,-0.07728642,0.06927235,0.029916165,-0.05038563,0.006388993,0.004797414,-0.07826116,0.018774696,-0.042779762,0.02954594,-0.011675843,0.032718644,-0.009256688,0.067655206,-0.028118782,-0.026903344,-0.14387448,0.0026201496,0.026571246,0.05906817,-0.04160195,0.0027989342,-0.11871287,-0.09010188,-0.023723463,-0.06750378,0.0038506198,0.018157804,-0.065961726,-0.071485795,-0.1205194,-0.025099827,-0.0011753824,-0.025850227,0.042625304,-0.03397236,-0.0052147736,0.0025903403,-0.04677946,0.07009958,-0.014874844,0.121384785,-0.06458527,0.031804625,-0.029966656,0.01488916,0.10432395,0.0128694335,-0.017377853,-0.07582352,0.012077827,0.019630881,0.05957209,-0.032720342,-0.047119625,-0.017485073,-0.06797555,-0.045616236,-0.01448269,-0.014741304,-0.064248994,-0.057714462,0.01487638,0.0051286747,0.000105519044,-0.068130836,-0.08954566,-0.015322058,-0.032214087,-0.06110069,-0.04991285,0.026290277,0.115675844,0.10939904,0.027130421,-0.051789574,0.05051396,-0.02166927,-0.091889605,0.065456904,0.038927514,-0.01650648,0.076273985,0.0026547855,-0.09544029,-0.010590825,-0.009069473,-0.0040624416,0.011580615,-0.07035773,-0.016029581,-0.0042466847,-0.04103972,0.027898414,-0.054178815,-0.012950773,-0.0129826395,0.04638247,-0.035145853,-0.0047835656,0.00055205374,-0.023906725,0.019697385,-0.092341706,0.053844117,-0.051163975,-0.026320893,-0.09214351,-0.023615045,-1.3498864e-34,-0.048667844,-0.08015571,-0.02240331,-0.006072251,0.05638279,0.07190069,-0.053646863,-0.009149563,0.100194514,0.009558107,0.006581657,0.038725644,-0.030833377,0.014624521,0.04895662,0.03160589,-0.018334728,0.04094842,-0.063473836,0.03035039,0.067989305,-0.0013933326,0.009243694,0.050671723,0.009409132,0.005778116,0.044169404,0.013727398,-0.06069443,-0.00198971,0.010786669,-0.06663625,-0.060575534,-0.07943784,-0.12197299,0.015635112,0.067870654,-0.012538558,-0.008571791,-0.04014067,-0.023742218,0.057845205,0.053372227,0.05981426,0.025279464,0.08130354,-0.0029848833,-0.045004893,-0.07820864,-0.022441689,-0.1001372,0.038734272,0.022381844,-0.029865816,0.06427472,0.11939155,0.06718441,-0.02532966,0.013090377,-0.0054002795,-0.03556851,0.046778064,-0.04380881,-0.03633029,0.08640463,0.06023997,0.010782865,-0.008888309,-0.014131912,-0.013858139,-0.014577206,-0.029342053,-0.0619427,0.016358754,0.012339049,-0.049630675,-0.092742145,0.025547141,0.0015705868,-0.015800195,0.00024007465,0.009243817,-0.02232219,-0.051768787,0.021100229,0.062842116,0.018514806,-0.045359567,0.0078948345,0.11019222,0.04818605,0.06807003,-0.010807117,-0.05300552,0.026880845,-5.4832444e-33,0.0030554081,0.11634377,-0.0064850016,0.049799744,0.094556846,0.038578983,-0.044117678,-0.009143126,0.007280561,0.030601462,-0.045851845,0.040536717,-0.022112526,-0.040874384,-0.04864078,0.0132579785,0.02645559,0.020387668,-0.08557249,0.04375685,0.0682282,0.07351379,0.033819243,0.0054670693,-0.08532578,-0.044574257,-0.03038342,-0.03259919,-0.039232068,0.03257994,0.029829714,0.016681073,-0.0007628494,0.0145105375,0.005137816,-0.05543969,-0.032329857,0.0047437446,-0.03603942,-0.050763812,-0.016126134,0.04561862,0.100613855,-0.08707964,-0.029923785,-0.028915565,-0.005728371,-0.08917974,-0.05289974,-0.0239674,0.07177382,0.025345415,-0.0374042,-0.06209851,0.042165674,-0.05815537,0.08813365,-0.04856246,-0.090559974,0.00045150964,0.041899752,0.039224632,-0.05989715,-0.038261283,-0.048070434,0.028219638,0.045809485,0.032475233,0.09440667,-0.038886998,-0.021289648,-0.053782802,0.057717912,-0.025405498,0.0017705098,0.0025109435,-0.051913597,0.02002908,0.0052305716,-0.0009494924,-0.13815612,0.005959545,0.0075552664,0.0003222514,-0.0984284,-0.027148912,-0.068113126,-0.060272526,-0.001969578,-0.051656295,-0.03042374,0.02516876,-0.00961558,0.011016636,0.04536189,-4.6829655e-08,0.01093044,-0.076007426,0.10138196,0.03185574,-0.011877303,0.004062455,-0.05558298,0.061161894,-0.047875836,-0.00039987994,-0.010506155,0.057751622,0.037813496,0.041454136,-0.05252598,-0.0880207,0.100056246,-0.016578794,-0.024980366,0.03144903,0.0763374,0.0114998575,0.0021932726,0.016733246,-0.059735492,0.051572744,-0.03257959,0.0010229087,-0.07383391,0.069080964,0.018615516,-0.021378571,0.03643948,-0.013149155,0.040483255,-0.12790418,0.008304601,0.056694236,0.024150115,0.13152811,-0.019401666,-0.16188337,0.07903611,0.13762024,0.011732571,-0.051009573,0.055416487,-0.048738528,0.013850313,0.015007538,0.039131857,-0.043990694,0.056201283,-0.04034365,-0.029498614,0.024799198,-0.0006495157,0.065578,0.022799412,0.0055841366,0.03741511,0.00556101,-0.04359979,0.008899249]
5	2	2025-09-27 14:30:36.804542	박현규	bakhg@skax.co.kr	# 업무 2: 병원 예약·진료 시스템 통합 주간 보고서\n\n## 1) 주간 요약\n이번 주에는 병원 예약·진료 시스템 통합 작업이 진행되었습니다. 주요 작업으로는 모바일 예약 화면의 버튼 크기 조정, 예약 UI 개선, 검사 결과 자동 연동 기능의 DB 샘플 테이블 작성, 병원 예약 UI에 캘린더 추가 등이 있었습니다. 그러나 예약 데이터 중복 저장 문제와 검사 결과 불러오는 속도 저하 문제가 발견되었습니다. 이를 해결하기 위해 예약 ID 외에 전화번호를 체크하는 방안과 DB 인덱스 추가를 고려하고 있습니다. SK헬스케어와의 회의에서는 UI 개선 현황과 DB 중복 이슈 해결 방안이 논의되었습니다.\n\n## 2) 사람별 주요 산출물\n- **박범준**: 병원 예약 UI 개선, 캘린더 추가, 검사 결과 자동 연동 기능 DB 샘플 테이블 작성.\n- **박현규**: 예약 데이터 중복 저장 문제 분석, DB 인덱스 추가 방안 검토, UI 개선 자료 준비.\n\n## 3) 협업 내역\n- **Slack**: 팀원 간의 실시간 커뮤니케이션 및 문제 해결 논의.\n- **Notion**: 프로젝트 진행 상황 및 회의 내용 정리.\n- **Outlook**: SK헬스케어와의 회의 일정 조율 및 이메일 소통.\n- **OneDrive**: hospital_reservation_integration.xlsx 파일 공유 및 협업.\n\n## 4) 리스크/이슈\n- **예약 데이터 중복 저장 문제**: 같은 환자가 여러 번 시도할 때 발생. 예약 ID와 전화번호를 함께 체크하는 방안 검토 중.\n- **검사 결과 불러오는 속도 저하**: DB 인덱스 추가로 조회 속도 개선 계획.\n- **UI 개선 필요**: '누구나 쉽게'라는 목표에 맞춰 글자 크기 조정 필요.\n\n## 5) 차주 계획 (2025-09-22 ~ 2025-09-26)\n- 예약 데이터 중복 방지 로직 수정 및 테스트.\n- 검사 결과 불러오는 속도 개선을 위한 DB 인덱스 추가.\n- UI 개선 작업 지속, 특히 글자 크기 조정.\n- SK헬스케어와의 협업을 통해 시스템 통합 작업 지속.\n- 회의에서 논의된 사항들 반영 및 후속 작업 진행.	[0.034047827,0.035842635,0.038600426,-0.00040547654,-0.04398047,-0.06343515,-0.008336959,0.041022517,-0.044888202,-0.038379356,0.091190964,-0.006699345,0.10985619,-0.06697471,0.02905657,-0.041934405,0.01271298,-0.0045945332,-0.074509315,0.071481094,0.028030114,-0.04630057,0.006074185,0.003356171,-0.07891574,0.01704113,-0.043333728,0.029036622,-0.012305952,0.032848302,-0.009184774,0.066025324,-0.031901103,-0.024749879,-0.14643487,0.00329653,0.026526172,0.059753418,-0.040884115,0.0015313782,-0.117991894,-0.08684123,-0.023778997,-0.068294026,0.004306809,0.02212633,-0.06754384,-0.06875279,-0.11925272,-0.02440989,-0.0026964634,-0.024521956,0.044582397,-0.031250328,-0.007326821,0.0082227355,-0.044927135,0.06907171,-0.01374967,0.121767424,-0.06250096,0.037029758,-0.028502932,0.015970474,0.106030814,0.01396599,-0.019410858,-0.07935396,0.012558944,0.018441588,0.062092766,-0.03214142,-0.051999375,-0.018869609,-0.070306584,-0.04890509,-0.01462232,-0.014778325,-0.06623704,-0.055608083,0.013299252,0.005709589,0.0014661578,-0.06883633,-0.091185555,-0.015561664,-0.030982757,-0.061120216,-0.050906952,0.025501767,0.114840835,0.11210143,0.02361806,-0.05093964,0.050949287,-0.024521034,-0.0910828,0.06473816,0.035016082,-0.016697075,0.07625073,0.0033016289,-0.094334215,-0.009076436,-0.008946816,-0.0041377554,0.012561769,-0.069468334,-0.012849124,-0.004478356,-0.040626157,0.026739428,-0.054531965,-0.009594404,-0.012902949,0.046023924,-0.033550967,-0.00538982,-0.0036900092,-0.024326384,0.019787295,-0.089790106,0.04892699,-0.04904297,-0.025317429,-0.095414914,-0.023273123,-2.709171e-34,-0.046073698,-0.08315586,-0.020078577,-0.0047221263,0.05707253,0.071954615,-0.053853422,-0.010270121,0.097035795,0.011385663,0.0033485685,0.035616815,-0.03138736,0.014434754,0.049420297,0.030931382,-0.019601496,0.037020423,-0.0636309,0.031032488,0.06851366,0.0009774683,0.007146606,0.04663674,0.007331374,0.0074590864,0.042454224,0.012657401,-0.060335983,-0.0031903216,0.00828583,-0.06702116,-0.061912514,-0.08083918,-0.123004496,0.015382609,0.070274964,-0.013386344,-0.008169296,-0.036245745,-0.021322316,0.05515474,0.053066995,0.060644194,0.02462923,0.0796741,-0.0015393001,-0.04563422,-0.08207917,-0.024128003,-0.09875091,0.03906171,0.023033367,-0.03190453,0.06777098,0.120951176,0.0699018,-0.023131797,0.014746092,-0.004459046,-0.03386184,0.04386095,-0.044040307,-0.033174027,0.083941445,0.060146317,0.01063143,-0.0079714265,-0.010101565,-0.01523421,-0.017010845,-0.030538484,-0.060375925,0.014644744,0.011597349,-0.049747385,-0.09596089,0.023838723,0.003429184,-0.014646329,0.004239117,0.007551569,-0.02043146,-0.051047638,0.023651857,0.06138074,0.016354391,-0.048354745,0.008452156,0.10931592,0.046972092,0.0668275,-0.011066282,-0.057270158,0.028251767,-5.366316e-33,0.006348795,0.11497676,-0.005678853,0.05045396,0.096949965,0.03743415,-0.044101786,-0.006107822,0.0023371524,0.033144966,-0.046392642,0.041064437,-0.018061772,-0.039538197,-0.04409012,0.013195932,0.025878424,0.023017833,-0.086778075,0.04500236,0.06981793,0.07161781,0.036781564,0.0032026072,-0.08567083,-0.045628253,-0.029113224,-0.033298776,-0.03963962,0.032259807,0.027672758,0.015929693,-0.00041150828,0.009630221,0.006724055,-0.05236872,-0.033877425,0.008043546,-0.037172846,-0.04941272,-0.015825978,0.044259265,0.10121266,-0.086088695,-0.03037225,-0.030202545,-0.0032163574,-0.085553996,-0.055125292,-0.021845182,0.06907305,0.026792683,-0.03388906,-0.06433521,0.044948302,-0.059073716,0.086725965,-0.048888464,-0.089260146,-0.00031589644,0.043212906,0.039601404,-0.05934755,-0.036735192,-0.04464941,0.030970564,0.04538337,0.034142725,0.093828775,-0.037781738,-0.022242079,-0.055642508,0.056719985,-0.02439351,0.005246036,0.0025517666,-0.055484354,0.018918538,0.0071151373,0.00013925193,-0.13814914,0.004933612,0.009160648,0.00068054686,-0.09971229,-0.02940153,-0.07052658,-0.06277115,-0.0018087465,-0.052395027,-0.028320428,0.024653738,-0.0063919662,0.008234904,0.04733846,-4.6129475e-08,0.009829617,-0.075278975,0.10418675,0.030185008,-0.010144141,0.0053415047,-0.051719956,0.056446362,-0.047027968,-0.0022509964,-0.010286491,0.054421056,0.043473557,0.041423023,-0.05293423,-0.08754439,0.104909845,-0.01918795,-0.025972359,0.033728708,0.07689222,0.011575686,0.002355572,0.017056609,-0.059582576,0.05040629,-0.032649867,0.0026812104,-0.075362414,0.06836093,0.019366533,-0.021311782,0.037371386,-0.011953573,0.03956853,-0.12677002,0.008686001,0.060590893,0.02159039,0.12854637,-0.02192896,-0.15945886,0.07758471,0.13887946,0.008928201,-0.048905265,0.059658635,-0.050650723,0.016105045,0.014461069,0.03938935,-0.04258014,0.05950091,-0.0402089,-0.032705583,0.024519598,-0.0023598243,0.06561379,0.019804422,0.005566563,0.034788027,0.0065737334,-0.04406025,0.0071856226]
6	2	2025-09-27 14:30:53.218948	박현규	bakhg@skax.co.kr	# 업무 2: 병원 예약·진료 시스템 통합 주간 보고서\n\n## 1) 주간 요약\n\n**Task 2 (병원 예약·진료 시스템 통합) 관련 진행 상황 요약:**\n\n- **모바일 예약 UI 개선:** 모바일 예약 화면의 버튼 크기를 조정하였으며, SK헬스케어 테스트 환경에서 긍정적인 반응을 얻었습니다. 그러나 글자 크기를 더 크게 조정할 필요가 있습니다.\n- **DB 중복 저장 문제:** 예약 데이터 중복 저장 문제가 발생하고 있으며, 특히 같은 환자가 여러 번 시도할 때 문제가 두드러집니다. 예약 ID의 고유값 설정이 제대로 작동하지 않는 것으로 보이며, 이번 주에 중복 방지 로직을 추가할 예정입니다.\n- **검사 결과 자동 연동 기능:** DB 샘플 테이블을 만들었으며, 연동이 잘 되면 UI와 연결할 계획입니다.\n- **캘린더 기능 추가:** 병원 예약 UI에 캘린더를 추가하여 날짜 선택이 더 직관적으로 개선되었습니다. 그러나 중복 예약 문제는 여전히 존재합니다.\n- **회의 일정:** SK헬스케어와의 회의가 목요일 오후 3시에 예정되어 있으며, UI 개선 현황 및 DB 중복 이슈 해결 방안을 보고할 예정입니다.\n- **야근 가능성:** 캘린더와 검사 결과 화면을 통합하는 작업이 쉽지 않아 야근이 필요할 수 있습니다.\n- **테스트 버전:** SK헬스케어 내부 계정으로 테스트 버전을 배포하였으며, UI 반응 속도는 괜찮으나 검사 결과 불러오는 속도가 느립니다. DB 인덱스를 추가하여 조회 속도를 개선할 계획입니다.\n- **OneDrive 자료:** hospital_reservation_integration.xlsx 파일을 OneDrive에 업로드하였으며, UI 스크린샷을 추가할 예정입니다.\n- **회의 준비:** UI 개선 자료와 DB 구조 수정안을 준비하여 SK헬스케어 담당자 앞에서 발표를 진행 중입니다.\n\n## 2) 사람별 주요 산출물\n\n- **박범준:** 모바일 예약 UI 개선, DB 중복 방지 로직 개발, 검사 결과 자동 연동 기능 DB 샘플 테이블 작성.\n- **박현규:** 캘린더 기능 추가, 검사 결과 화면 통합 작업, 병원 예약 시스템 테스트 버전 배포 및 속도 개선 방안 마련.\n\n## 3) 협업 내역\n\n- **Slack:** UI 개선 및 DB 중복 문제에 대한 실시간 논의.\n- **Notion:** 프로젝트 진행 상황 및 회의 준비 자료 정리.\n- **Outlook:** SK헬스케어와의 회의 일정 조율 및 관련 커뮤니케이션.\n- **OneDrive:** hospital_reservation_integration.xlsx 파일 공유 및 피드백 수렴.\n\n## 4) 리스크/이슈\n\n- **중복 예약 문제:** 예약 ID의 고유값 설정 문제로 인한 중복 예약 발생. 전화번호와 함께 체크하여 중복을 줄이는 방안을 고려 중.\n- **검사 결과 불러오기 속도:** 검사 결과 불러오는 속도가 느림. DB 인덱스 추가를 통해 개선 필요.\n\n## 5) 차주 계획\n\n(기간: 2025-09-22 ~ 2025-09-26)\n\n- **중복 예약 방지 로직 강화:** 예약 ID 외에 전화번호를 함께 체크하여 중복 예약 문제 해결.\n- **검사 결과 불러오기 속도 개선:** DB 인덱스 추가 및 최적화 작업.\n- **UI 개선 작업 지속:** 글자 크기 조정 및 추가적인 UI 개선 작업 진행.\n- **회의 결과 반영:** SK헬스케어 회의 피드백을 반영한 시스템 개선 작업.\n- **테스트 및 피드백 수렴:** 개선된 시스템에 대한 테스트 진행 및 피드백 수렴.	[0.011582703,0.018566538,0.06363129,-0.03616679,-0.015892327,-0.06626837,0.008700805,0.048580103,-0.050894834,-0.044198435,0.06551167,-0.000825427,0.10735287,-0.047888264,0.013834898,-0.04021897,0.043248367,-0.0040129325,-0.06962375,0.022915855,0.05305954,-0.06487026,0.014085747,-0.0080559915,-0.0711372,0.033231467,-0.06445674,0.01700765,-0.03364488,0.029734949,0.0019294355,0.03430461,-0.026543336,-0.029284718,-0.1029934,0.036868196,0.02338953,0.009793081,-0.051919583,-0.030728828,-0.12860145,-0.11629357,-0.0064696143,-0.09785717,0.03777035,0.032758243,-0.052249666,-0.104505956,-0.110536456,-0.048826445,-0.010436903,-0.033955522,0.045352533,-0.068541005,-0.022180665,0.016820282,-0.0077737365,0.09857459,-0.0046363794,0.07822643,-0.03733197,0.028041296,-0.04117515,0.022074308,0.103049956,-0.014464489,-0.0313082,-0.09188138,0.023278682,-0.010439508,0.04480733,-0.002774133,-0.005457794,-0.042945925,-0.039710276,-0.0815351,-0.047531877,0.003062256,-0.04694834,-0.0676811,0.07426634,-0.005113413,0.006529241,-0.045463942,-0.066073455,-0.0061444053,-0.050740954,-0.05466275,-0.02841144,0.025553597,0.13032871,0.09733581,0.02880032,-0.0010687739,0.04534216,-0.02750945,-0.10023927,0.07153223,0.026034744,-0.008705603,0.043023832,-0.016096873,-0.08719335,-0.045136984,0.002125294,0.029756319,0.009588878,-0.06498634,-0.017127892,-0.014775252,-0.0349726,-0.018503146,-0.06108211,-0.013105424,-0.027752588,0.026849484,-0.04909128,-0.0045000743,-0.021903718,0.0063180514,0.045971777,-0.07772063,0.05193535,-0.044533137,-0.0043957457,-0.081837155,0.017225306,-2.4221844e-34,-0.040875107,-0.07819656,-0.02775156,-0.000669684,0.024414549,0.03741511,-0.041225966,0.0044739745,0.08984847,-0.0009891446,0.027957628,0.010527082,-0.034617033,0.011924717,0.054918725,-0.0011228111,0.025259329,0.024660902,-0.07280502,0.049553014,0.08300683,0.007965623,0.0039989892,0.018700615,0.049406487,0.01592772,0.0640177,0.0054326267,-0.067266166,0.0093419645,-0.018065102,-0.060646668,-0.08933449,-0.040814765,-0.14195733,0.03995804,0.064999275,-0.042126063,0.025456654,-0.046033304,-0.02100036,0.06404108,0.061646502,0.030406825,0.01609542,0.06882393,-0.0076047895,-0.023567148,-0.04147199,-0.005165943,-0.07528348,0.021796104,0.010796789,-0.051111493,0.093869865,0.11420993,0.09168341,-0.015673088,0.043078795,0.022174153,-0.030438544,0.041921884,-0.06955256,-0.019082379,0.07271037,0.05634961,0.018950123,0.021261021,0.00903779,-0.02005513,-0.026954465,-0.046072252,-0.044059932,0.021520771,0.037363876,-0.04266513,-0.075204596,-0.021114467,-0.0008554443,0.0072790785,-0.008920718,0.023824908,-0.02722384,-0.0739829,0.014419155,0.06961327,0.0014592926,-0.07569415,-0.01928077,0.12043141,0.030162834,0.04733577,-0.04364386,-0.028159024,0.02332264,-5.451809e-33,0.008189866,0.1350466,-0.022089964,0.049711417,0.10439193,0.047975253,-0.027141409,-0.05772961,-0.018041713,0.06597618,-0.07459756,0.028324723,-0.050370257,-0.0307201,-0.040606443,0.0027474998,0.026812479,0.015167985,-0.1026128,0.039930187,0.057583936,0.117347896,0.0072210785,0.019018987,-0.075818144,-0.050351,-0.05337481,-0.0059897774,-0.02634338,0.010096538,0.022404738,-0.0031728386,-0.008517378,0.01693205,0.016018754,-0.044144854,-0.041659515,0.026734054,-0.038146272,-0.08234028,0.025943989,-0.0044618724,0.07189165,-0.07606516,-0.03430023,-0.018694496,-0.007598571,-0.072711706,-0.06199141,-0.021014899,0.04791183,0.020629128,-0.062253535,-0.07224847,0.072120674,-0.04005165,0.073530436,-0.07701033,-0.10306378,-0.046466235,0.07921996,0.04072859,-0.013766416,-0.028697336,8.722353e-05,0.018067645,0.060384143,0.0666076,0.051268138,-0.04192416,0.0037613169,-0.030713787,0.08389276,-0.022265589,-0.023121689,-0.017972361,-0.036446642,0.0220514,0.002728875,-0.006476534,-0.1480828,0.008857688,-0.0011747238,-0.009837038,-0.07973192,-0.022162756,-0.0570274,-0.057546027,0.019499337,-0.058844406,-0.006073408,0.042816956,0.025968522,0.0020404242,0.04214022,-4.6033676e-08,0.013905493,-0.044377293,0.054106615,0.023479402,-0.06655488,-0.01740879,-0.06332917,0.055821735,-0.02510526,-0.017397942,-0.010157585,-0.004718811,0.037623305,0.06239897,-0.0368701,-0.08854976,0.11678455,0.014218723,-0.035445727,0.013142752,0.10864026,-0.012467897,-0.041761268,0.034507286,-0.05906199,0.061498404,-0.07895748,0.030053364,-0.06992867,0.037888825,-0.0023740535,-0.018385785,-0.0017644551,0.0422086,0.049272433,-0.124602154,0.010784403,0.052777875,0.0073784697,0.10812511,-0.014085782,-0.12223923,0.08209456,0.13270488,0.015158377,-0.043998916,0.021529445,-0.08612294,0.015297627,0.029874483,0.022775711,-0.02749457,0.03460389,0.0055999337,0.022234645,0.055668756,0.018962607,0.029200876,0.002326189,0.02433593,0.025454307,0.0037552002,-0.062715285,0.02124081]
\.


--
-- Data for Name: slack; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.slack (id, receiver, sender, "timestamp", task_id, content, embedding) FROM stdin;
1	윤소현	서은수	2025-09-22 09:10:00	1	이번 주 결제 모듈 안정화 테스트 잘 진행되고 있어? SK 회사 보고에 들어갈 거라 중요해/n	\N
2	서은수	윤소현	2025-09-22 09:12:00	1	네, 온라인 쇼핑몰 결제 모듈 속도가 좀 더 빨라졌어요. 평균 0.8초 정도까지 줄였습니다/n	\N
3	윤소현	서은수	2025-09-22 09:15:00	1	좋네! 근데 어제 저녁에 서버 응답 지연 있었다던데 확인했어?/n	\N
4	서은수	윤소현	2025-09-22 09:17:00	1	네 확인했는데 동시 접속자가 몰려서 그런 것 같아요. 서버 로그 보니 CPU 95%까지 올라갔습니다/n	\N
5	윤소현	서은수	2025-09-22 09:20:00	1	검색 속도 개선도 같이 보고해줘. 이번 주 보고서는 임원진도 본대/n	\N
6	서은수	윤소현	2025-09-22 11:05:00	1	DB 인덱스 조정했더니 상품 검색 속도가 약 20% 개선됐습니다/n	\N
7	윤소현	서은수	2025-09-22 11:10:00	1	좋네. 근데 캐시 서버 적용은 언제쯤 가능할까?/n	\N
8	서은수	윤소현	2025-09-22 11:13:00	1	PoC는 다음 주쯤 시작 가능할 것 같아요. SK 회사 클라우드 자원 할당만 확정되면요/n	\N
9	윤소현	서은수	2025-09-22 13:00:00	1	점심 먹었어? 오늘 카페테리아 붐볐다더라/n	\N
10	서은수	윤소현	2025-09-22 13:02:00	1	네, 간단히 먹었어요. 온라인 쇼핑몰 검색 기능 생각하다 늦게 갔더니 자리 없더라고요/n	\N
11	윤소현	서은수	2025-09-22 15:45:00	1	오후 8시쯤 서버 지연 현상 또 나올까봐 걱정된다/n	\N
12	서은수	윤소현	2025-09-22 15:47:00	1	오늘은 모니터링을 강화해둘게요. 서버 자원 부족이 원인일 가능성이 크니까요/n	\N
13	윤소현	서은수	2025-09-22 16:10:00	1	SK 회사 회의실 예약했어? 내일 임원 보고 준비도 해야 해/n	\N
14	서은수	윤소현	2025-09-22 16:15:00	1	네, 오후 3시 회의실 확보했습니다. 보고 자료는 제가 정리해둘게요/n	\N
15	윤소현	서은수	2025-09-23 09:00:00	1	어제 저녁 서버 상태 어땠어?/n	\N
16	서은수	윤소현	2025-09-23 09:05:00	1	다행히 큰 지연은 없었습니다. 다만 CPU가 여전히 높아서 개선이 필요합니다/n	\N
17	윤소현	서은수	2025-09-23 10:20:00	1	결제 모듈 안정화 테스트 로그 업로드했습니다. OneDrive 확인해보세요/n	\N
18	서은수	윤소현	2025-09-23 10:25:00	1	좋아. 결과 요약해서 보고용으로 정리 부탁해/n	\N
19	윤소현	서은수	2025-09-23 12:30:00	1	오늘 점심 메뉴 추천 좀 해주세요. 머리 아파요 ㅋㅋ/n	\N
20	서은수	윤소현	2025-09-23 12:32:00	1	온라인 쇼핑몰에서 할인하던 김밥세트 어때? ㅋㅋ/n	\N
21	윤소현	서은수	2025-09-23 15:00:00	1	검색 속도 개선 내용도 보고서에 넣어야지/n	\N
22	서은수	윤소현	2025-09-23 15:05:00	1	네, DB 최적화 결과랑 캐시 서버 적용 계획 같이 정리하겠습니다/n	\N
23	윤소현	서은수	2025-09-24 09:10:00	1	결제 모듈 카드사 연동 테스트 중인데 한 군데서 오류 발생했습니다/n	\N
24	서은수	윤소현	2025-09-24 09:15:00	1	어느 카드사야? SK 회사랑 협의 필요할 수도 있겠다/n	\N
25	윤소현	서은수	2025-09-24 09:18:00	1	H카드 쪽입니다. 에러 로그 정리 중이에요/n	\N
26	서은수	윤소현	2025-09-24 14:00:00	1	회의 준비됐어? 임원 보고 자료 같이 확인하자/n	\N
27	윤소현	서은수	2025-09-24 14:05:00	1	네, 온라인 쇼핑몰 결제 모듈 개선 사항과 서버 응답 지연 이슈 정리했습니다/n	\N
28	서은수	윤소현	2025-09-25 09:30:00	1	어제 회의 피드백 괜찮았어/n	\N
29	윤소현	서은수	2025-09-25 09:35:00	1	네, 결제 모듈 속도 개선은 긍정적으로 봤습니다. 다만 서버 지연은 조속히 해결해야 한다고 했습니다/n	\N
30	서은수	윤소현	2025-09-26 10:00:00	1	이번 주 보고서 최종 버전 마무리했어?/n	\N
31	박범준	박현규	2025-09-22 09:05:00	2	어제 모바일 예약 화면 버튼 크기 조정했는데, SK헬스케어 테스트 환경에서 반응 괜찮았어?/n	\N
32	박현규	박범준	2025-09-22 09:07:00	2	응 괜찮아 보였어. 다만 글자 크기는 조금 더 크게 해야 할 듯./n	\N
33	박범준	박현규	2025-09-22 09:10:00	2	알겠어. 예약 UI 개선 목표가 ‘누구나 쉽게’니까 글자도 맞춰야지./n	\N
34	박현규	박범준	2025-09-22 09:20:00	2	DB 로그 보니까 예약 데이터 중복 저장되는 케이스가 또 발생했어./n특히 같은 환자가 여러 번 시도할 때./n	\N
35	박범준	박현규	2025-09-22 09:23:00	2	헐, 그거 큰 문제네. 예약 ID 고유값 설정 제대로 안 먹힌 건가?/n	\N
36	박현규	박범준	2025-09-22 09:30:00	2	아직 샘플 데이터에는 중복 방지 로직이 없어서 그래. 이번 주에 수정할게./n	\N
37	박범준	박현규	2025-09-22 10:00:00	2	점심 뭐 먹을래? 병원 근처 식당 가자. 어제부터 UI 코드 붙잡느라 머리 아프네./n	\N
38	박현규	박범준	2025-09-22 10:05:00	2	좋아, 삼계탕 어때? SK헬스케어 회의실 근처에 맛집 있잖아./n	\N
39	박범준	박현규	2025-09-22 14:10:00	2	검사 결과 자동 연동 기능 DB 샘플 테이블 만들었어. 오후에 확인해줄래?/n	\N
40	박현규	박범준	2025-09-22 14:15:00	2	오케이. 연동 잘 되면 UI 쪽에도 바로 연결해볼게./n	\N
41	박범준	박현규	2025-09-23 09:00:00	2	어제 병원 예약 UI에 캘린더 추가했어. 이제 날짜 선택이 훨씬 보기 좋을 거야./n	\N
42	박현규	박범준	2025-09-23 09:05:00	2	좋네. 그럼 DB에서 예약 시간과 매칭 잘 되는지만 확인하면 돼./n	\N
43	박범준	박현규	2025-09-23 11:00:00	2	근데 중복 예약 문제 아직 완전히 해결 안 됐어. 새로운 테스트 케이스에서 또 떴어./n	\N
44	박현규	박범준	2025-09-23 11:05:00	2	그럼 예약 ID 외에 전화번호도 같이 체크하도록 바꿀까?/n	\N
45	박범준	박현규	2025-09-23 13:00:00	2	좋은 생각이야. 고유값을 두 개 이상 묶으면 중복 줄일 수 있지./n	\N
46	박현규	박범준	2025-09-23 15:20:00	2	SK헬스케어 쪽에서 이번 주 목요일에 회의 일정 잡았어. 오후 3시래./n	\N
47	박범준	박현규	2025-09-23 15:25:00	2	오케이. UI 개선 현황이랑 DB 중복 이슈 해결 방안 같이 보고하자./n	\N
48	박현규	박범준	2025-09-23 17:00:00	2	야, 오늘 야근해야 할지도 몰라. 캘린더랑 검사 결과 화면 같이 붙이는 중인데 쉽지 않네./n	\N
49	박범준	박현규	2025-09-23 17:05:00	2	나도 DB 정리 때문에 남아야 할 듯. 우리 둘 다 병원 예약 시스템 붙잡고 있네./n	\N
50	박현규	박범준	2025-09-24 09:30:00	2	어제 테스트 버전 올렸어. SK헬스케어 내부 계정으로 로그인해봐./n	\N
51	박범준	박현규	2025-09-24 09:40:00	2	봤어. UI 반응 속도 괜찮아. 다만 검사 결과 불러오는 게 조금 느려./n	\N
52	박현규	박범준	2025-09-24 10:00:00	2	DB 인덱스 추가하면 빨라질까?/n	\N
53	박범준	박현규	2025-09-24 10:05:00	2	응, 인덱스 처리하면 조회 속도 개선될 거야. 이번 주 안에 반영할게./n	\N
54	박현규	박범준	2025-09-24 13:20:00	2	OneDrive에 hospital_reservation_integration.xlsx 올렸어. 확인해줘./n	\N
55	박범준	박현규	2025-09-24 13:25:00	2	봤어. 정리 잘했네. UI 스크린샷도 넣으면 좋을 듯./n	\N
56	박현규	박범준	2025-09-25 09:00:00	2	오늘 회의 준비됐어? SK헬스케어 담당자 앞에서 발표해야 해./n	\N
57	박범준	박현규	2025-09-25 09:10:00	2	응. UI 개선 자료랑 DB 구조 수정안 다 챙겼어./n	\N
58	박현규	박범준	2025-09-25 15:00:00	2	회의 시작했어. 지금 예약 화면 시연 중./n	\N
59	박범준	박현규	2025-09-25 15:30:00	2	담당자가 검사 결과 자동 연동 부분 관심 많네. 속도 빨리 개선해야겠다./n	\N
60	박현규	박범준	2025-09-26 11:00:00	2	이번 주 마무리로 중복 예약 방지 로직 다시 점검하자. 병원 예약 시스템 핵심이잖아./n	\N
\.


--
-- Data for Name: task; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.task (id, task_uuid, description) FROM stdin;
1	t001	온라인 쇼핑몰 시스템 구축
2	t002	병원 예약·진료 시스템 통합
\.


--
-- Name: administer_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.administer_id_seq', 5, false);


--
-- Name: employee_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.employee_id_seq', 7, false);


--
-- Name: notion_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.notion_id_seq', 3, false);


--
-- Name: onedrive_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.onedrive_id_seq', 3, false);


--
-- Name: outlook_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.outlook_id_seq', 5, false);


--
-- Name: participant_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.participant_id_seq', 3, false);


--
-- Name: report_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.report_id_seq', 6, true);


--
-- Name: slack_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.slack_id_seq', 61, false);


--
-- Name: task_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.task_id_seq', 3, false);


--
-- Name: administer administer_email_key; Type: CONSTRAINT; Schema: project; Owner: postgres
--

ALTER TABLE ONLY project.administer
    ADD CONSTRAINT administer_email_key UNIQUE (email);


--
-- Name: administer administer_pkey; Type: CONSTRAINT; Schema: project; Owner: postgres
--

ALTER TABLE ONLY project.administer
    ADD CONSTRAINT administer_pkey PRIMARY KEY (id);


--
-- Name: employee employee_email_key; Type: CONSTRAINT; Schema: project; Owner: postgres
--

ALTER TABLE ONLY project.employee
    ADD CONSTRAINT employee_email_key UNIQUE (email);


--
-- Name: employee employee_pkey; Type: CONSTRAINT; Schema: project; Owner: postgres
--

ALTER TABLE ONLY project.employee
    ADD CONSTRAINT employee_pkey PRIMARY KEY (id);


--
-- Name: notion notion_pkey; Type: CONSTRAINT; Schema: project; Owner: postgres
--

ALTER TABLE ONLY project.notion
    ADD CONSTRAINT notion_pkey PRIMARY KEY (id);


--
-- Name: onedrive onedrive_pkey; Type: CONSTRAINT; Schema: project; Owner: postgres
--

ALTER TABLE ONLY project.onedrive
    ADD CONSTRAINT onedrive_pkey PRIMARY KEY (id);


--
-- Name: outlook outlook_pkey; Type: CONSTRAINT; Schema: project; Owner: postgres
--

ALTER TABLE ONLY project.outlook
    ADD CONSTRAINT outlook_pkey PRIMARY KEY (id);


--
-- Name: participant participant_pkey; Type: CONSTRAINT; Schema: project; Owner: postgres
--

ALTER TABLE ONLY project.participant
    ADD CONSTRAINT participant_pkey PRIMARY KEY (id);


--
-- Name: report report_pkey; Type: CONSTRAINT; Schema: project; Owner: postgres
--

ALTER TABLE ONLY project.report
    ADD CONSTRAINT report_pkey PRIMARY KEY (id);


--
-- Name: slack slack_pkey; Type: CONSTRAINT; Schema: project; Owner: postgres
--

ALTER TABLE ONLY project.slack
    ADD CONSTRAINT slack_pkey PRIMARY KEY (id);


--
-- Name: task task_pkey; Type: CONSTRAINT; Schema: project; Owner: postgres
--

ALTER TABLE ONLY project.task
    ADD CONSTRAINT task_pkey PRIMARY KEY (id);


--
-- Name: administer administer_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.administer
    ADD CONSTRAINT administer_email_key UNIQUE (email);


--
-- Name: administer administer_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.administer
    ADD CONSTRAINT administer_pkey PRIMARY KEY (id);


--
-- Name: employee employee_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employee
    ADD CONSTRAINT employee_email_key UNIQUE (email);


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
-- Name: report report_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.report
    ADD CONSTRAINT report_pkey PRIMARY KEY (id);


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

\unrestrict 1im2ABbn6N6XxgZGfLymCsfnbTHnKF0ttKxV1uM0hqZz4yKSRI0b9dfobYeQAgh

