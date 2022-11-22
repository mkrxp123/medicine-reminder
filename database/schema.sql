CREATE TABLE 
    if NOT EXISTS public."Users"(
        "LineID" character(33) COLLATE pg_catalog."default" NOT NULL,
        "UserName" character varying(50) COLLATE pg_catalog."default" NOT NULL,
        CONSTRAINT "Users_pkey" PRIMARY KEY ("LineID")
    );

CREATE TABLE 
    if NOT EXISTS public."Reminders"(
        "Title" character varying(50) COLLATE pg_catalog."default" NOT NULL,
        "ReminderID" character(4) COLLATE pg_catalog."default" NOT NULL,
        "UserName" character varying(50) COLLATE pg_catalog."default" NOT NULL,
        "Prescription" bytea,
        "Picture" bytea,
        "TotalTimes" integer NOT NULL,
        CONSTRAINT "Reminders_pkey" PRIMARY KEY ("ReminderID")
    );

CREATE TABLE 
    if NOT EXISTS public."RemindTimes"(
        "ReminderID" character(4) COLLATE pg_catalog."default" NOT NULL,
        "RemindTime" time without time zone NOT NULL,
        CONSTRAINT "RemindTimes_pkey" PRIMARY KEY ("ReminderID", "RemindTime")
    );
