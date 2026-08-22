import { MigrationInterface, QueryRunner } from "typeorm";

export class CreateProductsSchema1787429345431 implements MigrationInterface {
    name = 'CreateProductsSchema1787429345431'

    public async up(queryRunner: QueryRunner): Promise<void> {
        await queryRunner.query(`CREATE TYPE "public"."product_audit_action" AS ENUM('creado', 'actualizado', 'eliminado', 'cambio_estado')`);
        await queryRunner.query(`CREATE TABLE "product_audit_log" ("audit_id" uuid NOT NULL DEFAULT uuid_generate_v4(), "product_id" uuid NOT NULL, "action" "public"."product_audit_action" NOT NULL, "field_name" character varying(60), "old_value" text, "new_value" text, "changed_by" character varying(120) NOT NULL, "changed_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), CONSTRAINT "PK_0430113f8bd8cfeed53ba863e6d" PRIMARY KEY ("audit_id"))`);
        await queryRunner.query(`CREATE TABLE "suppliers" ("supplier_id" uuid NOT NULL DEFAULT uuid_generate_v4(), "name" character varying(150) NOT NULL, "contact_email" character varying(150), "contact_phone" character varying(40), CONSTRAINT "PK_a2692f796d16e0a30040860112a" PRIMARY KEY ("supplier_id"))`);
        await queryRunner.query(`CREATE TABLE "product_suppliers" ("product_id" uuid NOT NULL, "supplier_id" uuid NOT NULL, "cost_price" numeric(12,2) NOT NULL, CONSTRAINT "chk_product_suppliers_cost_non_negative" CHECK ("cost_price" >= 0), CONSTRAINT "PK_0417cd29610720c9b12d82eb46b" PRIMARY KEY ("product_id", "supplier_id"))`);
        await queryRunner.query(`CREATE TABLE "warehouses" ("warehouse_id" uuid NOT NULL DEFAULT uuid_generate_v4(), "name" character varying(120) NOT NULL, "address" character varying(200) NOT NULL, "city" character varying(100) NOT NULL, CONSTRAINT "PK_02702eca36a8790626984c68de1" PRIMARY KEY ("warehouse_id"))`);
        await queryRunner.query(`CREATE TABLE "inventory" ("inventory_id" uuid NOT NULL DEFAULT uuid_generate_v4(), "variant_id" uuid NOT NULL, "warehouse_id" uuid NOT NULL, "quantity_on_hand" integer NOT NULL DEFAULT '0', "reorder_level" integer NOT NULL DEFAULT '0', "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), CONSTRAINT "uq_inventory_variant_warehouse" UNIQUE ("variant_id", "warehouse_id"), CONSTRAINT "chk_inventory_reorder_level_non_negative" CHECK ("reorder_level" >= 0), CONSTRAINT "chk_inventory_quantity_non_negative" CHECK ("quantity_on_hand" >= 0), CONSTRAINT "PK_711db979ad954f0ab33e3eea53a" PRIMARY KEY ("inventory_id"))`);
        await queryRunner.query(`CREATE TABLE "product_variants" ("variant_id" uuid NOT NULL DEFAULT uuid_generate_v4(), "product_id" uuid NOT NULL, "sku" character varying(64) NOT NULL, "color" character varying(50), "size" character varying(50), "price" numeric(12,2) NOT NULL, "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), CONSTRAINT "UQ_46f236f21640f9da218a063a866" UNIQUE ("sku"), CONSTRAINT "chk_product_variants_price_non_negative" CHECK ("price" >= 0), CONSTRAINT "PK_4c6116b1b96c664f518916e92a2" PRIMARY KEY ("variant_id"))`);
        await queryRunner.query(`CREATE TYPE "public"."product_status" AS ENUM('borrador', 'activo', 'descontinuado')`);
        await queryRunner.query(`CREATE TABLE "products" ("product_id" uuid NOT NULL DEFAULT uuid_generate_v4(), "name" character varying(150) NOT NULL, "description" text, "brand" character varying(100), "category_id" uuid NOT NULL, "status" "public"."product_status" NOT NULL DEFAULT 'borrador', "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), CONSTRAINT "PK_a8940a4bf3b90bd7ac15c8f4dd9" PRIMARY KEY ("product_id"))`);
        await queryRunner.query(`CREATE TABLE "categories" ("category_id" uuid NOT NULL DEFAULT uuid_generate_v4(), "parent_category_id" uuid, "name" character varying(120) NOT NULL, "slug" character varying(140) NOT NULL, CONSTRAINT "UQ_420d9f679d41281f282f5bc7d09" UNIQUE ("slug"), CONSTRAINT "PK_51615bef2cea22812d0dcab6e18" PRIMARY KEY ("category_id"))`);
        await queryRunner.query(`ALTER TABLE "seeder_log" ALTER COLUMN "executed_at" SET DEFAULT now()`);
        await queryRunner.query(`ALTER TABLE "product_audit_log" ADD CONSTRAINT "FK_7bcbac2c69c4f8fec6441585635" FOREIGN KEY ("product_id") REFERENCES "products"("product_id") ON DELETE CASCADE ON UPDATE NO ACTION`);
        await queryRunner.query(`ALTER TABLE "product_suppliers" ADD CONSTRAINT "FK_c1b61c92463463f577fac49b95c" FOREIGN KEY ("product_id") REFERENCES "products"("product_id") ON DELETE CASCADE ON UPDATE NO ACTION`);
        await queryRunner.query(`ALTER TABLE "product_suppliers" ADD CONSTRAINT "FK_be4a36f37c7345ab274ec4656d2" FOREIGN KEY ("supplier_id") REFERENCES "suppliers"("supplier_id") ON DELETE CASCADE ON UPDATE NO ACTION`);
        await queryRunner.query(`ALTER TABLE "inventory" ADD CONSTRAINT "FK_ceba910e3505fc54c3c7f92c943" FOREIGN KEY ("variant_id") REFERENCES "product_variants"("variant_id") ON DELETE CASCADE ON UPDATE NO ACTION`);
        await queryRunner.query(`ALTER TABLE "inventory" ADD CONSTRAINT "FK_5d9d73a4c5fe0202714a51e4649" FOREIGN KEY ("warehouse_id") REFERENCES "warehouses"("warehouse_id") ON DELETE RESTRICT ON UPDATE NO ACTION`);
        await queryRunner.query(`ALTER TABLE "product_variants" ADD CONSTRAINT "FK_6343513e20e2deab45edfce1316" FOREIGN KEY ("product_id") REFERENCES "products"("product_id") ON DELETE CASCADE ON UPDATE NO ACTION`);
        await queryRunner.query(`ALTER TABLE "products" ADD CONSTRAINT "FK_9a5f6868c96e0069e699f33e124" FOREIGN KEY ("category_id") REFERENCES "categories"("category_id") ON DELETE RESTRICT ON UPDATE NO ACTION`);
        await queryRunner.query(`ALTER TABLE "categories" ADD CONSTRAINT "FK_de08738901be6b34d2824a1e243" FOREIGN KEY ("parent_category_id") REFERENCES "categories"("category_id") ON DELETE SET NULL ON UPDATE NO ACTION`);
    }

    public async down(queryRunner: QueryRunner): Promise<void> {
        await queryRunner.query(`ALTER TABLE "categories" DROP CONSTRAINT "FK_de08738901be6b34d2824a1e243"`);
        await queryRunner.query(`ALTER TABLE "products" DROP CONSTRAINT "FK_9a5f6868c96e0069e699f33e124"`);
        await queryRunner.query(`ALTER TABLE "product_variants" DROP CONSTRAINT "FK_6343513e20e2deab45edfce1316"`);
        await queryRunner.query(`ALTER TABLE "inventory" DROP CONSTRAINT "FK_5d9d73a4c5fe0202714a51e4649"`);
        await queryRunner.query(`ALTER TABLE "inventory" DROP CONSTRAINT "FK_ceba910e3505fc54c3c7f92c943"`);
        await queryRunner.query(`ALTER TABLE "product_suppliers" DROP CONSTRAINT "FK_be4a36f37c7345ab274ec4656d2"`);
        await queryRunner.query(`ALTER TABLE "product_suppliers" DROP CONSTRAINT "FK_c1b61c92463463f577fac49b95c"`);
        await queryRunner.query(`ALTER TABLE "product_audit_log" DROP CONSTRAINT "FK_7bcbac2c69c4f8fec6441585635"`);
        await queryRunner.query(`ALTER TABLE "seeder_log" ALTER COLUMN "executed_at" SET DEFAULT CURRENT_TIMESTAMP`);
        await queryRunner.query(`DROP TABLE "categories"`);
        await queryRunner.query(`DROP TABLE "products"`);
        await queryRunner.query(`DROP TYPE "public"."product_status"`);
        await queryRunner.query(`DROP TABLE "product_variants"`);
        await queryRunner.query(`DROP TABLE "inventory"`);
        await queryRunner.query(`DROP TABLE "warehouses"`);
        await queryRunner.query(`DROP TABLE "product_suppliers"`);
        await queryRunner.query(`DROP TABLE "suppliers"`);
        await queryRunner.query(`DROP TABLE "product_audit_log"`);
        await queryRunner.query(`DROP TYPE "public"."product_audit_action"`);
    }

}
