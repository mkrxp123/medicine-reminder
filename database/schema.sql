CREATE TABLE 
    if NOT EXISTS public."Users"(
        "LineID" character(33) COLLATE pg_catalog."default" NOT NULL,
        "UserName" character varying(50) COLLATE pg_catalog."default" NOT NULL,
        CONSTRAINT "Users_pkey" PRIMARY KEY ("LineID")
    );

CREATE TABLE 
	if NOT EXISTS public."Reminders"(
    	"Title" character varying(50) COLLATE pg_catalog."default" NOT NULL,
    	"ReminderID" integer NOT NULL,
    	"UserName" character varying(50) COLLATE pg_catalog."default" NOT NULL,
        "Picture" bytea,
        "Hospital" character varying(50) COLLATE pg_catalog."default",
        "GroupID" character(33) COLLATE pg_catalog."default" NOT NULL,
        "GetMedicine" boolean NOT NULL,
        CONSTRAINT "Reminders_pkey1" PRIMARY KEY ("ReminderID")
	);

CREATE TABLE 
    if NOT EXISTS public."RemindTimes"(
        "ReminderID" integer NOT NULL,
        "RemindTime" time without time zone NOT NULL,
        "RemindDate" date NOT NULL,
        CONSTRAINT "RemindTimes_pkey1" PRIMARY KEY ("ReminderID", "RemindTime", "RemindDate")
    );

CREATE TABLE 
    if NOT EXISTS public."RemindGroups"(
        "GroupID" character(33) COLLATE pg_catalog."default" NOT NULL,
        "GroupName" character varying(50) COLLATE pg_catalog."default" NOT NULL,
        CONSTRAINT "RemindGroups_pkey" PRIMARY KEY ("GroupID")
    );
