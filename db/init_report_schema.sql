--
-- PostgreSQL database dump
--

\restrict s1v3aLtYj0YtZBtZffQdccatPqIexvfXdfso8ij8w4AliADdV1TsvhkP9R0C0Tf

-- Dumped from database version 18.1
-- Dumped by pg_dump version 18.1

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: report_artifact; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.report_artifact (
    artifact_id bigint NOT NULL,
    report_id bigint NOT NULL,
    format text NOT NULL,
    file_path text NOT NULL,
    citations jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.report_artifact OWNER TO postgres;

--
-- Name: report_artifact_artifact_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.report_artifact_artifact_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.report_artifact_artifact_id_seq OWNER TO postgres;

--
-- Name: report_artifact_artifact_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.report_artifact_artifact_id_seq OWNED BY public.report_artifact.artifact_id;


--
-- Name: report_request; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.report_request (
    report_id bigint NOT NULL,
    company_id bigint NOT NULL,
    template text NOT NULL,
    as_of_date date,
    status public.report_status DEFAULT 'PENDING'::public.report_status NOT NULL,
    requested_by text,
    params jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.report_request OWNER TO postgres;

--
-- Name: report_request_report_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.report_request_report_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.report_request_report_id_seq OWNER TO postgres;

--
-- Name: report_request_report_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.report_request_report_id_seq OWNED BY public.report_request.report_id;


--
-- Name: report_artifact artifact_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.report_artifact ALTER COLUMN artifact_id SET DEFAULT nextval('public.report_artifact_artifact_id_seq'::regclass);


--
-- Name: report_request report_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.report_request ALTER COLUMN report_id SET DEFAULT nextval('public.report_request_report_id_seq'::regclass);


--
-- Name: report_artifact report_artifact_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.report_artifact
    ADD CONSTRAINT report_artifact_pkey PRIMARY KEY (artifact_id);


--
-- Name: report_request report_request_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.report_request
    ADD CONSTRAINT report_request_pkey PRIMARY KEY (report_id);


--
-- Name: idx_report_company; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_report_company ON public.report_request USING btree (company_id, created_at DESC);


--
-- Name: report_artifact report_artifact_report_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.report_artifact
    ADD CONSTRAINT report_artifact_report_id_fkey FOREIGN KEY (report_id) REFERENCES public.report_request(report_id) ON DELETE CASCADE;


--
-- Name: report_request report_request_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.report_request
    ADD CONSTRAINT report_request_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.company(company_id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict s1v3aLtYj0YtZBtZffQdccatPqIexvfXdfso8ij8w4AliADdV1TsvhkP9R0C0Tf

