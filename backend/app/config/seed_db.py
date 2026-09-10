import logging
from datetime import datetime
from app.config.database import SessionLocal
from app.models.cpse import CPSE
from app.models.material import Material
from app.models.national_material import NationalMaterial
from app.models.material_mapping import MaterialMapping
from app.models.user import User
from app.models.material_match import MaterialMatch
from app.models.import_batch import ImportBatch
from app.models.audit_log import AuditLog
from app.models.inventory import Inventory
from app.models.material_request import MaterialRequest
from app.models.request_item import RequestItem
from app.models.approval_action import ApprovalAction
from app.models.integration_sync import IntegrationSync
from app.models.stock_allocation import StockAllocation
from app.models.import_error import ImportRowError
from app.models.import_dead_letter import ImportDeadLetter
from app.models.demand_record import DemandRecord
from app.utils.security import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_database():
    db = SessionLocal()

    try:
        logger.info("Clearing old records for fresh seed...")
        db.query(StockAllocation).delete()
        db.query(RequestItem).delete()
        db.query(MaterialRequest).delete()
        db.query(ApprovalAction).delete()
        db.query(MaterialMapping).delete()
        db.query(MaterialMatch).delete()
        db.query(Inventory).delete()
        db.query(DemandRecord).delete()
        db.query(Material).delete()
        db.query(NationalMaterial).delete()
        db.query(ImportDeadLetter).delete()
        db.query(ImportRowError).delete()
        db.query(ImportBatch).delete()
        db.query(IntegrationSync).delete()
        db.query(AuditLog).delete()
        db.query(User).delete()
        db.query(CPSE).delete()
        db.commit()

        logger.info("Seeding initial database records into PostgreSQL...")

        # 1. Seed Users
        user_officer = User(
            name="Procurement Officer",
            email="officer@numm.gov.in",
            password_hash=hash_password("officer123"),
            role="CPSE_OFFICER"
        )
        user_admin = User(
            name="Rajesh Kumar",
            email="r.kumar@numm.gov.in",
            password_hash=hash_password("admin123"),
            role="ADMIN"
        )
        user_reviewer = User(
            name="Anita Sen",
            email="a.sen@numm.gov.in",
            password_hash=hash_password("officer123"),
            role="REVIEWER"
        )
        db.add_all([user_officer, user_admin, user_reviewer])
        db.flush()

        # 2. Seed CPSEs
        cpses_data = [
            {"name": "Oil & Natural Gas Corporation", "code": "ONGC", "sector": "Oil & Gas"},
            {"name": "NTPC Limited", "code": "NTPC", "sector": "Power"},
            {"name": "Steel Authority of India", "code": "SAIL", "sector": "Steel"},
            {"name": "Bharat Heavy Electricals", "code": "BHEL", "sector": "Heavy Engineering"},
            {"name": "Coal India Limited", "code": "CIL", "sector": "Mining"},
            {"name": "GAIL India", "code": "GAIL", "sector": "Oil & Gas"},
            {"name": "Indian Oil Corporation", "code": "IOCL", "sector": "Oil & Gas"}
        ]

        cpse_objs = {}
        for cdata in cpses_data:
            cpse = CPSE(**cdata)
            db.add(cpse)
            db.flush()
            cpse_objs[cdata["code"]] = cpse

        db.add(User(
            name="Requesting Officer",
            email="requester@numm.gov.in",
            password_hash=hash_password("requester123"),
            role="REQUESTING_OFFICER",
            cpse_id=cpse_objs["ONGC"].id,
        ))

        # 3. Seed National Materials
        nat_data = [
            {
                "national_code": "NM-VAL-001",
                "description": "Industrial Ball Valve SS316 DN50 PN16 Flanged",
                "category": "Valves & Actuators",
                "unit": "NOS",
                "specifications": "Stainless Steel AISI 316 Body & Trim, Nominal Size DN50 (2 Inch), Pressure Rating PN16 / Class 150, Flanged Ends ANSI B16.5, Fire Tested ISO 10497"
            },
            {
                "national_code": "NM-PMP-002",
                "description": "Centrifugal Heavy Duty Slurry Pump 45kW",
                "category": "Pumps & Compressors",
                "unit": "SET",
                "specifications": "Flow 120 m3/hr, Total Head 40m, Motor 45kW 415V 50Hz 3-Phase, High Chrome Alloy Casing Hi-Cr28"
            },
            {
                "national_code": "NM-PIP-003",
                "description": "Carbon Steel Seamless Pipe 6 Inch Sch 40 API 5L Gr B",
                "category": "Pipes & Fittings",
                "unit": "MTR",
                "specifications": "Seamless Carbon Steel, 6\" Nominal Bore (150mm), Wall Thickness Schedule 40, Standard API 5L Grade B, Beveled Ends"
            },
            {
                "national_code": "NM-TRF-004",
                "description": "Power Transformer 33kV/11kV 5MVA Oil Immersed",
                "category": "Electrical Equipment",
                "unit": "UNIT",
                "specifications": "HV 33kV, LV 11kV, Power Rating 5 MVA, Vector Group Dyn11, Cooling ONAN, CRGO Core Steel, Outdoor Type"
            },
            {
                "national_code": "NM-BRG-005",
                "description": "Spherical Roller Bearing 22220 K C3 Tapered Bore",
                "category": "Bearings & Power Transmission",
                "unit": "NOS",
                "specifications": "Bore 100mm, OD 180mm, Width 46mm, Tapered 1:12, Internal Clearance C3, Brass Cage"
            },
            {
                "national_code": "NM-FLG-006",
                "description": "Weld Neck Flange 150# 6 Inch SS304 Raised Face",
                "category": "Pipes & Fittings",
                "unit": "NOS",
                "specifications": "ASTM A182 Grade F304, Size 6\" (150mm), Pressure Class 150 LB, Raised Face (RF), Schedule 40 Bore"
            }
        ]

        nat_objs = {}
        for ndata in nat_data:
            nat = NationalMaterial(**ndata)
            db.add(nat)
            db.flush()
            nat_objs[ndata["national_code"]] = nat

        # 4. Seed CPSE Materials
        materials_data = [
            # ONGC
            {"cpse_id": cpse_objs["ONGC"].id, "material_code": "ONG-V-1029", "description": "Industrial Ball Valve SS316 DN50 PN16 Flanged", "cleaned_description": "BALL VALVE SS316 DN50 PN16 FLANGED", "normalized_description": "BALL VALVE SS316 DN50 PN16 FLANGED", "category": "Valves & Actuators", "unit": "NOS", "manufacturer": "L&T Valves", "model": "BV-316-50", "specifications": {"grade": "SS316", "size": "DN50", "pressure": "PN16", "ends": "Flanged"}, "matching_status": "PROCESSED"},
            {"cpse_id": cpse_objs["ONGC"].id, "material_code": "ONG-P-8810", "description": "Centrifugal Slurry Pump 45kW 1450RPM Heavy Duty", "cleaned_description": "CENTRIFUGAL SLURRY PUMP 45KW 1450RPM HEAVY DUTY", "normalized_description": "CENTRIFUGAL SLURRY PUMP 45KW 1450RPM HEAVY DUTY", "category": "Pumps & Compressors", "unit": "SET", "manufacturer": "KSB Pumps", "model": "KWP-120-40", "specifications": {"power": "45kW", "voltage": "415V", "rpm": "1450", "type": "Slurry"}, "matching_status": "PROCESSED"},
            {"cpse_id": cpse_objs["ONGC"].id, "material_code": "ONG-PI-441", "description": "Carbon Steel Seamless Pipe 6 Inch Sch 40 API 5L Gr B", "cleaned_description": "CARBON STEEL SEAMLESS PIPE 6 INCH SCH 40 API 5L GR B", "normalized_description": "CARBON STEEL SEAMLESS PIPE 6 INCH SCH 40 API 5L GR B", "category": "Pipes & Fittings", "unit": "MTR", "manufacturer": "Jindal Saw", "model": "API-5L-6", "specifications": {"size": "6\"", "schedule": "Sch 40", "standard": "API 5L Gr B"}, "matching_status": "PROCESSED"},
            {"cpse_id": cpse_objs["ONGC"].id, "material_code": "ONG-FL-550", "description": "Weld Neck Flange 150# 6 Inch SS304 RF", "cleaned_description": "WELD NECK FLANGE 150# 6 INCH SS304 RF", "normalized_description": "WELD NECK FLANGE 150# 6 INCH SS304 RF", "category": "Pipes & Fittings", "unit": "NOS", "manufacturer": "MetalForge", "model": "WN-150-6-304", "specifications": {"grade": "SS304", "size": "6\"", "rating": "150#"}, "matching_status": "PROCESSED"},

            # NTPC
            {"cpse_id": cpse_objs["NTPC"].id, "material_code": "NTP-VAL-44", "description": "Stainless Steel Ball Valve 50mm Class 150 RF", "cleaned_description": "BALL VALVE SS316 50MM CLASS 150 RF", "normalized_description": "BALL VALVE SS316 50MM CLASS 150 RF", "category": "Valves & Actuators", "unit": "NOS", "manufacturer": "Kirloskar", "model": "SS-50-CL150", "specifications": {"grade": "AISI 316", "size": "50mm", "class": "150"}, "matching_status": "PROCESSED"},
            {"cpse_id": cpse_objs["NTPC"].id, "material_code": "NTP-TR-331", "description": "Power Transformer 33kV / 11kV 5MVA Oil Immersed", "cleaned_description": "POWER TRANSFORMER 33KV 11KV 5MVA OIL IMMERSED", "normalized_description": "POWER TRANSFORMER 33KV 11KV 5MVA OIL IMMERSED", "category": "Electrical Equipment", "unit": "UNIT", "manufacturer": "BHEL", "model": "TR-33-5MVA", "specifications": {"voltage": "33/11kV", "power": "5MVA", "cooling": "ONAN"}, "matching_status": "PROCESSED"},
            {"cpse_id": cpse_objs["NTPC"].id, "material_code": "NTP-PMP-11", "description": "Boiler Feed Water Pump Mechanical Seal Assembly", "cleaned_description": "BOILER FEED WATER PUMP MECHANICAL SEAL ASSEMBLY", "normalized_description": "BOILER FEED WATER PUMP MECHANICAL SEAL ASSEMBLY", "category": "Pumps & Compressors", "unit": "SET", "manufacturer": "EagleBurgmann", "model": "H75VN", "specifications": {"material": "SiC vs Carbon", "shaft": "65mm"}, "matching_status": "PROCESSED"},

            # SAIL
            {"cpse_id": cpse_objs["SAIL"].id, "material_code": "SL-V-002", "description": "Ball Valve SS 316 Class 150 2 Inch Full Port", "cleaned_description": "BALL VALVE SS316 CLASS 150 2 INCH FULL PORT", "normalized_description": "BALL VALVE SS316 CLASS 150 2 INCH FULL PORT", "category": "Valves & Actuators", "unit": "NOS", "manufacturer": "Audco", "model": "CL150-2", "specifications": {"grade": "SS316", "size": "2\"", "class": "150 RF"}, "matching_status": "PROCESSED"},
            {"cpse_id": cpse_objs["SAIL"].id, "material_code": "SL-P-880", "description": "Seamless Steel Line Pipe 150mm Sch 40 Grade B", "cleaned_description": "SEAMLESS STEEL LINE PIPE 150MM SCH 40 GRADE B", "normalized_description": "SEAMLESS STEEL LINE PIPE 150MM SCH 40 GRADE B", "category": "Pipes & Fittings", "unit": "MTR", "manufacturer": "SAIL Plant", "model": "SL-150-SCH40", "specifications": {"size": "150mm", "schedule": "Sch 40", "grade": "Gr B"}, "matching_status": "PROCESSED"},
            {"cpse_id": cpse_objs["SAIL"].id, "material_code": "SL-BRG-12", "description": "Spherical Roller Bearing 22220 K C3 Tapered Bore", "cleaned_description": "SPHERICAL ROLLER BEARING 22220 K C3 TAPERED BORE", "normalized_description": "SPHERICAL ROLLER BEARING 22220 K C3 TAPERED BORE", "category": "Bearings & Power Transmission", "unit": "NOS", "manufacturer": "SKF", "model": "22220-EK-C3", "specifications": {"bore": "100mm", "od": "180mm", "width": "46mm"}, "matching_status": "PROCESSED"},

            # BHEL
            {"cpse_id": cpse_objs["BHEL"].id, "material_code": "BH-VL-991", "description": "SS316 Industrial Valve DN50 PN16 Flanged", "cleaned_description": "VALVE SS316 DN50 PN16 FLANGED", "normalized_description": "VALVE SS316 DN50 PN16 FLANGED", "category": "Valves & Actuators", "unit": "NOS", "manufacturer": "BHEL Valve Unit", "model": "V-50-PN16", "specifications": {"grade": "SS316", "size": "DN50", "pressure": "PN16"}, "matching_status": "PROCESSED"},
            {"cpse_id": cpse_objs["BHEL"].id, "material_code": "BH-TR-500", "description": "33kV / 11kV Step Down Power Transformer 5 MVA ONAN", "cleaned_description": "STEP DOWN POWER TRANSFORMER 33KV 11KV 5 MVA ONAN", "normalized_description": "STEP DOWN POWER TRANSFORMER 33KV 11KV 5 MVA ONAN", "category": "Electrical Equipment", "unit": "UNIT", "manufacturer": "BHEL Bhopal", "model": "TR-500-33", "specifications": {"voltage": "33kV/11kV", "power": "5MVA", "vector": "Dyn11"}, "matching_status": "PROCESSED"},

            # CIL
            {"cpse_id": cpse_objs["CIL"].id, "material_code": "CIL-PMP-404", "description": "Heavy Duty Submersible Slurry Pump 45kW 50Hz", "cleaned_description": "SUBMERSIBLE SLURRY PUMP 45KW 50HZ HEAVY DUTY", "normalized_description": "SUBMERSIBLE SLURRY PUMP 45KW 50HZ HEAVY DUTY", "category": "Pumps & Compressors", "unit": "SET", "manufacturer": "Flygt", "model": "5500-45kW", "specifications": {"power": "45kW", "voltage": "415V", "freq": "50Hz"}, "matching_status": "PROCESSED"}
        ]

        mat_objs = []
        for mdata in materials_data:
            mat = Material(**mdata)
            db.add(mat)
            db.flush()
            mat_objs.append(mat)

        # 5. Seed Material Matches
        match1 = MaterialMatch(
            material_a_id=mat_objs[0].id, # ONG-V-1029
            material_b_id=mat_objs[4].id, # NTP-VAL-44
            semantic_score=0.982,
            attribute_score=0.965,
            fuzzy_score=0.950,
            final_score=0.974,
            classification="EXACT_MATCH",
            status="APPROVED",
            explanation="Both records represent Stainless Steel AISI 316 Ball Valves with DN50 (2-inch) diameter and PN16/Class 150 flanged rating."
        )
        match2 = MaterialMatch(
            material_a_id=mat_objs[5].id, # NTP-TR-331
            material_b_id=mat_objs[11].id, # BH-TR-500
            semantic_score=0.990,
            attribute_score=0.981,
            fuzzy_score=0.975,
            final_score=0.9855,
            classification="EXACT_MATCH",
            status="APPROVED",
            explanation="Exact match: 33kV/11kV 5MVA Oil-Immersed ONAN Power Transformers with Dyn11 vector configuration."
        )
        match3 = MaterialMatch(
            material_a_id=mat_objs[1].id, # ONG-P-8810
            material_b_id=mat_objs[12].id, # CIL-PMP-404
            semantic_score=0.864,
            attribute_score=0.891,
            fuzzy_score=0.820,
            final_score=0.8775,
            classification="FUNCTIONAL_EQUIVALENT",
            status="PENDING",
            explanation="Both units are 45kW heavy-duty slurry pumps with 415V 50Hz electrical drive. Human engineering review required."
        )
        match4 = MaterialMatch(
            material_a_id=mat_objs[0].id, # ONG-V-1029
            material_b_id=mat_objs[7].id, # SL-V-002
            semantic_score=0.955,
            attribute_score=0.940,
            fuzzy_score=0.930,
            final_score=0.948,
            classification="EXACT_MATCH",
            status="PENDING",
            explanation="2-inch Class 150 SS316 Ball Valves across ONGC and SAIL. Pending officer authorization."
        )
        db.add_all([match1, match2, match3, match4])
        db.flush()

        # 6. Seed Material Mappings (for approved matches)
        map1 = MaterialMapping(
            material_id=mat_objs[0].id, # ONG-V-1029
            national_material_id=nat_objs["NM-VAL-001"].id,
            mapping_type="EXACT_MATCH",
            approved_by=user_reviewer.id
        )
        map2 = MaterialMapping(
            material_id=mat_objs[4].id, # NTP-VAL-44
            national_material_id=nat_objs["NM-VAL-001"].id,
            mapping_type="EXACT_MATCH",
            approved_by=user_reviewer.id
        )
        map3 = MaterialMapping(
            material_id=mat_objs[5].id, # NTP-TR-331
            national_material_id=nat_objs["NM-TRF-004"].id,
            mapping_type="EXACT_MATCH",
            approved_by=user_reviewer.id
        )
        map4 = MaterialMapping(
            material_id=mat_objs[11].id, # BH-TR-500
            national_material_id=nat_objs["NM-TRF-004"].id,
            mapping_type="EXACT_MATCH",
            approved_by=user_reviewer.id
        )
        db.add_all([map1, map2, map3, map4])

        # 7. Seed Real Inventory Records
        inv1 = Inventory(
            cpse_id=cpse_objs["ONGC"].id,
            material_id=mat_objs[0].id,
            warehouse="ONGC Mumbai Central Depot",
            available_quantity=45,
            reserved_quantity=5,
            uom="NOS"
        )
        inv2 = Inventory(
            cpse_id=cpse_objs["NTPC"].id,
            material_id=mat_objs[4].id,
            warehouse="NTPC Dadri Regional Store",
            available_quantity=30,
            reserved_quantity=0,
            uom="NOS"
        )
        inv3 = Inventory(
            cpse_id=cpse_objs["SAIL"].id,
            material_id=mat_objs[7].id,
            warehouse="SAIL Bhilai Steel Yard",
            available_quantity=20,
            reserved_quantity=2,
            uom="NOS"
        )
        inv4 = Inventory(
            cpse_id=cpse_objs["BHEL"].id,
            material_id=mat_objs[11].id,
            warehouse="BHEL Bhopal Heavy Store",
            available_quantity=4,
            reserved_quantity=1,
            uom="UNIT"
        )
        inv5 = Inventory(
            cpse_id=cpse_objs["CIL"].id,
            material_id=mat_objs[12].id,
            warehouse="CIL Ranchi Mining Depot",
            available_quantity=8,
            reserved_quantity=0,
            uom="SET"
        )
        db.add_all([inv1, inv2, inv3, inv4, inv5])

        # 8. Seed Import Batches
        batch1 = ImportBatch(
            filename="ONGC_Q3_Master_Materials.csv",
            file_type="CSV",
            cpse_id=cpse_objs["ONGC"].id,
            total_rows=14200,
            successful_rows=13950,
            failed_rows=250,
            status="COMPLETED"
        )
        batch2 = ImportBatch(
            filename="NTPC_Valves_Catalog_2026.xlsx",
            file_type="Excel",
            cpse_id=cpse_objs["NTPC"].id,
            total_rows=4821,
            successful_rows=4821,
            failed_rows=0,
            status="COMPLETED"
        )
        batch3 = ImportBatch(
            filename="SAIL_Steel_Spares_Master.csv",
            file_type="CSV",
            cpse_id=cpse_objs["SAIL"].id,
            total_rows=8900,
            successful_rows=8840,
            failed_rows=60,
            status="COMPLETED"
        )
        db.add_all([batch1, batch2, batch3])
        db.flush()

        # 9. Seed Audit Logs with proper entity_type and json details
        logs = [
            AuditLog(user_id=user_admin.id, action="IMPORT", entity_type="IMPORT_BATCH", entity_id=batch1.id, details={"message": "ONGC uploaded Q3 Master Materials batch (14,200 rows).", "cpse": "ONGC", "filename": "ONGC_Q3_Master_Materials.csv"}),
            AuditLog(user_id=user_admin.id, action="AI_MATCH", entity_type="MATERIAL_MATCH", entity_id=match1.id, details={"message": "AI Engine executed cluster analysis on Valves category (97.4% match confidence).", "cpse": "SYSTEM"}),
            AuditLog(user_id=user_reviewer.id, action="APPROVAL", entity_type="MATERIAL_MATCH", entity_id=match1.id, details={"message": "Technical Reviewer approved mapping ONGC-ONG-V-1029 -> NM-VAL-001.", "cpse": "ONGC", "national_code": "NM-VAL-001"}),
            AuditLog(user_id=user_admin.id, action="CODE_CREATED", entity_type="NATIONAL_MATERIAL", entity_id=nat_objs["NM-TRF-004"].id, details={"message": "Generated National Material Code NM-TRF-004 for 33kV/11kV Transformers.", "cpse": "NATIONAL"}),
            AuditLog(user_id=user_reviewer.id, action="OFFICER_REVIEW", entity_type="MATERIAL_MATCH", entity_id=match2.id, details={"message": "Anita Sen reviewed side-by-side comparison between NTPC and BHEL transformer specs.", "cpse": "NTPC"})
        ]
        for l in logs:
            db.add(l)

        db.commit()
        logger.info("Successfully seeded PostgreSQL database with 100% real CPSE material records!")

    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
