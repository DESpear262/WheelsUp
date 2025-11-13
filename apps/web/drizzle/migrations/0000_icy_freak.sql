CREATE TABLE "attributes" (
	"id" serial PRIMARY KEY NOT NULL,
	"school_id" varchar(50) NOT NULL,
	"amenities" jsonb,
	"equipment" jsonb,
	"special_programs" jsonb,
	"certifications" jsonb,
	"partnerships" jsonb,
	"awards" jsonb,
	"custom_attributes" jsonb,
	"social_media" jsonb,
	"online_presence" jsonb,
	"operational_notes" jsonb,
	"source_type" varchar(50) NOT NULL,
	"source_url" text NOT NULL,
	"extracted_at" timestamp with time zone DEFAULT now() NOT NULL,
	"confidence" real NOT NULL,
	"extractor_version" varchar(20) NOT NULL,
	"snapshot_id" varchar(50) NOT NULL,
	"last_updated" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "metrics" (
	"id" serial PRIMARY KEY NOT NULL,
	"school_id" varchar(50) NOT NULL,
	"training" jsonb,
	"operational" jsonb,
	"experience" jsonb,
	"accreditation" jsonb,
	"financial" jsonb,
	"metrics_last_updated" timestamp with time zone,
	"data_sources" jsonb,
	"sample_size" integer,
	"overall_reliability_score" real,
	"overall_quality_score" real,
	"source_type" varchar(50) NOT NULL,
	"source_url" text NOT NULL,
	"extracted_at" timestamp with time zone DEFAULT now() NOT NULL,
	"confidence" real NOT NULL,
	"extractor_version" varchar(20) NOT NULL,
	"snapshot_id" varchar(50) NOT NULL,
	"last_updated" timestamp with time zone DEFAULT now() NOT NULL,
	"is_current" boolean DEFAULT true NOT NULL
);
--> statement-breakpoint
CREATE TABLE "pricing" (
	"id" serial PRIMARY KEY NOT NULL,
	"school_id" varchar(50) NOT NULL,
	"hourly_rates" jsonb,
	"package_pricing" jsonb,
	"program_costs" jsonb,
	"additional_fees" jsonb,
	"currency" varchar(3) DEFAULT 'USD' NOT NULL,
	"price_last_updated" timestamp with time zone,
	"value_inclusions" jsonb,
	"scholarships_available" boolean,
	"source_type" varchar(50) NOT NULL,
	"source_url" text NOT NULL,
	"extracted_at" timestamp with time zone DEFAULT now() NOT NULL,
	"confidence" real NOT NULL,
	"extractor_version" varchar(20) NOT NULL,
	"snapshot_id" varchar(50) NOT NULL,
	"last_updated" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "programs" (
	"id" serial PRIMARY KEY NOT NULL,
	"school_id" varchar(50) NOT NULL,
	"program_id" varchar(50) NOT NULL,
	"details" jsonb NOT NULL,
	"is_active" boolean DEFAULT true NOT NULL,
	"seasonal_availability" text,
	"source_type" varchar(50) NOT NULL,
	"source_url" text NOT NULL,
	"extracted_at" timestamp with time zone DEFAULT now() NOT NULL,
	"confidence" real NOT NULL,
	"extractor_version" varchar(20) NOT NULL,
	"snapshot_id" varchar(50) NOT NULL,
	"last_updated" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "programs_program_id_unique" UNIQUE("program_id")
);
--> statement-breakpoint
CREATE TABLE "schools" (
	"id" serial PRIMARY KEY NOT NULL,
	"school_id" varchar(50) NOT NULL,
	"name" varchar(200) NOT NULL,
	"description" text,
	"specialties" jsonb,
	"contact" jsonb,
	"location" jsonb,
	"accreditation" jsonb,
	"operations" jsonb,
	"google_rating" real,
	"google_review_count" integer,
	"yelp_rating" real,
	"source_type" varchar(50) NOT NULL,
	"source_url" text NOT NULL,
	"extracted_at" timestamp with time zone DEFAULT now() NOT NULL,
	"confidence" real NOT NULL,
	"extractor_version" varchar(20) NOT NULL,
	"snapshot_id" varchar(50) NOT NULL,
	"last_updated" timestamp with time zone DEFAULT now() NOT NULL,
	"is_active" boolean DEFAULT true NOT NULL,
	CONSTRAINT "schools_school_id_unique" UNIQUE("school_id")
);
--> statement-breakpoint
ALTER TABLE "attributes" ADD CONSTRAINT "attributes_school_id_schools_school_id_fk" FOREIGN KEY ("school_id") REFERENCES "public"."schools"("school_id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "metrics" ADD CONSTRAINT "metrics_school_id_schools_school_id_fk" FOREIGN KEY ("school_id") REFERENCES "public"."schools"("school_id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "pricing" ADD CONSTRAINT "pricing_school_id_schools_school_id_fk" FOREIGN KEY ("school_id") REFERENCES "public"."schools"("school_id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "programs" ADD CONSTRAINT "programs_school_id_schools_school_id_fk" FOREIGN KEY ("school_id") REFERENCES "public"."schools"("school_id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
CREATE INDEX "attributes_school_id_idx" ON "attributes" USING btree ("school_id");--> statement-breakpoint
CREATE INDEX "attributes_snapshot_idx" ON "attributes" USING btree ("snapshot_id");--> statement-breakpoint
CREATE INDEX "metrics_school_id_idx" ON "metrics" USING btree ("school_id");--> statement-breakpoint
CREATE INDEX "metrics_snapshot_idx" ON "metrics" USING btree ("snapshot_id");--> statement-breakpoint
CREATE INDEX "metrics_reliability_score_idx" ON "metrics" USING btree ("overall_reliability_score");--> statement-breakpoint
CREATE INDEX "metrics_quality_score_idx" ON "metrics" USING btree ("overall_quality_score");--> statement-breakpoint
CREATE INDEX "pricing_school_id_idx" ON "pricing" USING btree ("school_id");--> statement-breakpoint
CREATE INDEX "pricing_snapshot_idx" ON "pricing" USING btree ("snapshot_id");--> statement-breakpoint
CREATE UNIQUE INDEX "programs_program_id_idx" ON "programs" USING btree ("program_id");--> statement-breakpoint
CREATE INDEX "programs_school_id_idx" ON "programs" USING btree ("school_id");--> statement-breakpoint
CREATE INDEX "programs_type_idx" ON "programs" USING btree ("details");--> statement-breakpoint
CREATE INDEX "programs_snapshot_idx" ON "programs" USING btree ("snapshot_id");--> statement-breakpoint
CREATE UNIQUE INDEX "schools_school_id_idx" ON "schools" USING btree ("school_id");--> statement-breakpoint
CREATE INDEX "schools_name_idx" ON "schools" USING btree ("name");--> statement-breakpoint
CREATE INDEX "schools_location_idx" ON "schools" USING btree ("location");--> statement-breakpoint
CREATE INDEX "schools_accreditation_idx" ON "schools" USING btree ("accreditation");--> statement-breakpoint
CREATE INDEX "schools_snapshot_idx" ON "schools" USING btree ("snapshot_id");