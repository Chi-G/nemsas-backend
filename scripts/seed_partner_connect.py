import asyncio
import os
import sys
import json
from datetime import datetime, timezone
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

# Ensure the app directory is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.core.security import get_password_hash
from app.partners.models import PartnerUser, PartnerPledge, PartnerFacility, PartnerAmbulance
from app.models.state import State
from app.models.lga import LGA
from app.models.ward import Ward
from app.models.hospital import Hospital
from app.models.ambulance_type import AmbulanceType

# Helper to find a state, lga, ward, hospital, and ambulance type
async def find_state(db: AsyncSession, json_id: int, name: str) -> Optional[State]:
    res = await db.execute(select(State).where(State.id == json_id))
    state = res.scalar_one_or_none()
    if not state:
        res = await db.execute(select(State).where(State.name.ilike(name)))
        state = res.scalar_one_or_none()
    if not state:
        res = await db.execute(select(State).limit(1))
        state = res.scalar_one_or_none()
    return state

async def find_lga(db: AsyncSession, json_id: int, name: str, state_id: int) -> Optional[LGA]:
    res = await db.execute(select(LGA).where(LGA.id == json_id))
    lga = res.scalar_one_or_none()
    if not lga:
        res = await db.execute(select(LGA).where(LGA.name.ilike(name), LGA.state_id == state_id))
        lga = res.scalar_one_or_none()
    if not lga:
        res = await db.execute(select(LGA).where(LGA.state_id == state_id).limit(1))
        lga = res.scalar_one_or_none()
    return lga

async def find_ward(db: AsyncSession, json_id: int, name: str, lga_id: int) -> Optional[Ward]:
    res = await db.execute(select(Ward).where(Ward.id == json_id))
    ward = res.scalar_one_or_none()
    if not ward:
        res = await db.execute(select(Ward).where(Ward.name.ilike(name), Ward.lga_id == lga_id))
        ward = res.scalar_one_or_none()
    if not ward:
        res = await db.execute(select(Ward).where(Ward.lga_id == lga_id).limit(1))
        ward = res.scalar_one_or_none()
    return ward

async def find_hospital(db: AsyncSession, json_id: int, name: str) -> Optional[Hospital]:
    res = await db.execute(select(Hospital).where(Hospital.id == json_id))
    hosp = res.scalar_one_or_none()
    if not hosp:
        res = await db.execute(select(Hospital).where(Hospital.name.ilike(name)))
        hosp = res.scalar_one_or_none()
    if not hosp:
        res = await db.execute(select(Hospital).limit(1))
        hosp = res.scalar_one_or_none()
    return hosp

async def find_ambulance_type(db: AsyncSession, name: str) -> Optional[AmbulanceType]:
    res = await db.execute(select(AmbulanceType).where(AmbulanceType.name.ilike(name)))
    type_obj = res.scalar_one_or_none()
    if not type_obj:
        res = await db.execute(select(AmbulanceType).limit(1))
        type_obj = res.scalar_one_or_none()
    return type_obj

async def seed_partner_data():
    async with SessionLocal() as db:
        print("🌱 Seeding Partner User...")
        # Create partner user: johndoe@gmail.com / Password@1
        res = await db.execute(select(PartnerUser).where(PartnerUser.email == "johndoe@gmail.com"))
        user = res.scalar_one_or_none()
        if not user:
            user = PartnerUser(
                first_name="John",
                last_name="Doe",
                email="johndoe@gmail.com",
                hashed_password=get_password_hash("Password@1"),
                phone_number="08012345678",
                organisation_name="John Doe Corp",
                is_active=True,
                is_verified=True
            )
            db.add(user)
            await db.flush()
            print(f"✅ Created Verified Partner User: johndoe@gmail.com")
        else:
            if not user.is_verified:
                user.is_verified = True
                await db.flush()
                print(f"✅ Updated Partner User: johndoe@gmail.com to be verified")
            else:
                print("Partner User already exists and is verified.")

        partner_user_id = user.id

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        connect_dir = os.path.join(base_dir, "nemsas-connect")

        # 1. Seed Pledges
        pledges_file = os.path.join(connect_dir, "pledges.json")
        if os.path.exists(pledges_file):
            print("🌱 Seeding Pledges...")
            with open(pledges_file, "r") as f:
                data = json.load(f)
                items = data.get("data", {}).get("list", {}).get("data", [])
                for i, item in enumerate(items):
                    item_id = item.get("id")
                    # Skip if already exists
                    exist_check = await db.execute(select(PartnerPledge).where(PartnerPledge.id == item_id))
                    if exist_check.scalar_one_or_none():
                        continue

                    state_json = item.get("state") or {}
                    lga_json = item.get("lga") or {}
                    ward_json = item.get("ward") or {}
                    fac_json = item.get("facility") or {}
                    amb_type_json = item.get("ambulanceType") or {}

                    state = await find_state(db, state_json.get("id"), state_json.get("name"))
                    lga = await find_lga(db, lga_json.get("id"), lga_json.get("name"), state.id if state else 1)
                    ward = await find_ward(db, ward_json.get("id"), ward_json.get("name"), lga.id if lga else 1)
                    hosp = await find_hospital(db, fac_json.get("id"), fac_json.get("name"))
                    amb_type = await find_ambulance_type(db, amb_type_json.get("name", "BLS"))

                    pledge_date = datetime.strptime(item["pledgeDate"], "%Y-%m-%d").replace(tzinfo=timezone.utc) if item.get("pledgeDate") else None
                    delivery_date = datetime.strptime(item["deliveryDate"], "%Y-%m-%d").replace(tzinfo=timezone.utc) if item.get("deliveryDate") else None

                    plg = PartnerPledge(
                        id=item_id,
                        pledge_id_str=item.get("pledgeId"),
                        contact_details=item.get("contactDetails"),
                        donor_name=item.get("donorName"),
                        pledge_type=item.get("pledgeType"),
                        number_of_ambulance=item.get("numberOfAmbulance", 0),
                        ambulance_type_id=amb_type.id if amb_type else None,
                        state_id=state.id if state else None,
                        lga_id=lga.id if lga else None,
                        ward_id=ward.id if ward else None,
                        facility_id=hosp.id if hosp else None,
                        pledge_date=pledge_date,
                        delivery_date=delivery_date,
                        status=item.get("status", "pending"),
                        added_by_id=partner_user_id
                    )
                    db.add(plg)
            await db.commit()
            print("✅ Seeding Pledges completed!")

        # 2. Seed Facilities
        facilities_file = os.path.join(connect_dir, "health-facility.json")
        if os.path.exists(facilities_file):
            print("🌱 Seeding Health Facilities...")
            with open(facilities_file, "r") as f:
                data = json.load(f)
                items = data.get("data", {}).get("data", [])
                for item in items:
                    item_id = item.get("id")
                    # Skip if already exists
                    exist_check = await db.execute(select(PartnerFacility).where(PartnerFacility.id == item_id))
                    if exist_check.scalar_one_or_none():
                        continue

                    state_json = item.get("state") or {}
                    lga_json = item.get("lga") or {}
                    ward_json = item.get("ward") or {}

                    state = await find_state(db, state_json.get("id"), state_json.get("name"))
                    lga = await find_lga(db, lga_json.get("id"), lga_json.get("name"), state.id if state else 1)
                    ward = await find_ward(db, ward_json.get("id"), ward_json.get("name"), lga.id if lga else 1)

                    devices = ",".join(item.get("communicationDevices", []))

                    fac = PartnerFacility(
                        id=item_id,
                        facility_id_str=item.get("facilityId"),
                        facility_name=item.get("facilityName"),
                        facility_type=item.get("facilityType"),
                        facility_location=item.get("facilityLocation"),
                        ownership_type=item.get("ownershipType"),
                        communication_devices=devices,
                        number_of_ambulance=item.get("numberOfAmbulance", 0),
                        address=item.get("facilityAddress"),
                        contact_information=item.get("facilityContactInformation"),
                        state_id=state.id if state else None,
                        lga_id=lga.id if lga else None,
                        ward_id=ward.id if ward else None,
                        status=item.get("status", "pending"),
                        added_by_id=partner_user_id
                    )
                    db.add(fac)
            await db.commit()
            print("✅ Seeding Health Facilities completed!")

        # 3. Seed Ambulances
        ambulances_file = os.path.join(connect_dir, "ambulance-list.json")
        if os.path.exists(ambulances_file):
            print("🌱 Seeding Partner Ambulances...")
            with open(ambulances_file, "r") as f:
                data = json.load(f)
                items = data.get("data", {}).get("ambulances", {}).get("data", [])
                for item in items:
                    item_id = item.get("id")
                    # Skip if already exists
                    exist_check = await db.execute(select(PartnerAmbulance).where(PartnerAmbulance.id == item_id))
                    if exist_check.scalar_one_or_none():
                        continue

                    basic = item.get("basicInformation") or {}
                    tech = item.get("technicalSpecification") or {}
                    equip = item.get("equipmentInventory") or {}
                    comp = item.get("complianceAndDocumentation") or {}
                    status_json = item.get("status") or {}

                    state_json = basic.get("state") or {}
                    lga_json = basic.get("lga") or {}
                    ward_json = basic.get("ward") or {}
                    fac_json = basic.get("facility") or {}

                    state = await find_state(db, state_json.get("id"), state_json.get("name"))
                    lga = await find_lga(db, lga_json.get("id"), lga_json.get("name"), state.id if state else 1)
                    ward = await find_ward(db, ward_json.get("id"), ward_json.get("name"), lga.id if lga else 1)
                    hosp = await find_hospital(db, fac_json.get("id"), fac_json.get("name"))

                    comm_devices = ",".join(tech.get("communicationDevices", []))
                    equipments = ",".join(equip.get("equipments", []))

                    road_date = datetime.strptime(comp["roadWorthinessAssessmentDate"], "%Y-%m-%d").replace(tzinfo=timezone.utc) if comp.get("roadWorthinessAssessmentDate") else None
                    insp_date = datetime.strptime(comp["lastInspectionDate"], "%Y-%m-%d").replace(tzinfo=timezone.utc) if comp.get("lastInspectionDate") else None
                    maint_date = datetime.strptime(comp["nextScheduledMaintenance"], "%Y-%m-%d").replace(tzinfo=timezone.utc) if comp.get("nextScheduledMaintenance") else None
                    ins_exp_date = datetime.strptime(comp["insuranceExpirationDate"], "%Y-%m-%d").replace(tzinfo=timezone.utc) if comp.get("insuranceExpirationDate") else None

                    amb = PartnerAmbulance(
                        id=item_id,
                        ambulance_id_str=item.get("ambulanceId"),
                        plate_number=basic.get("plateNumber"),
                        make=basic.get("make"),
                        model=basic.get("model"),
                        year=basic.get("year"),
                        accreditation_type=basic.get("accreditationType"),
                        state_id=state.id if state else None,
                        lga_id=lga.id if lga else None,
                        ward_id=ward.id if ward else None,
                        facility_id=hosp.id if hosp else None,
                        vehicle_ownership_type=basic.get("vehicleOwnershipType"),
                        driver_name=basic.get("driverName"),
                        contact_number=basic.get("contactNumber"),
                        fuel_type=tech.get("fuelType"),
                        other_fuel_type_option=tech.get("otherFuelTypeOption", ""),
                        fuel_capacity=tech.get("fuelCapicity"),
                        communication_devices=comm_devices,
                        other_communication_device_option=tech.get("otherCommunicationDeviceOption", ""),
                        latitude=tech.get("latitude"),
                        longitude=tech.get("longitude"),
                        equipments=equipments,
                        road_worthiness_assessment_date=road_date,
                        road_worthiness_status=comp.get("roadWorthinessStatus"),
                        last_inspection_date=insp_date,
                        next_scheduled_maintenance=maint_date,
                        inspection_notes=comp.get("inspectionNotes"),
                        insurance_provider=comp.get("insuranceProvider"),
                        insurance_expiration_date=ins_exp_date,
                        status=status_json.get("status", "active"),
                        is_out_for_maintenance=status_json.get("isOutForMaintenance", False),
                        is_out_of_service=status_json.get("isOutOfService", False),
                        added_by_id=partner_user_id
                    )
                    db.add(amb)
            await db.commit()
            print("✅ Seeding Partner Ambulances completed!")

        # Sync table sequences
        tables = ["partner_users", "partner_pledges", "partner_facilities", "partner_ambulances"]
        for t in tables:
            try:
                await db.execute(text(f"SELECT setval('{t}_id_seq', COALESCE((SELECT MAX(id) FROM {t}), 1));"))
                await db.commit()
                print(f"🔄 Synced sequence for {t}")
            except Exception as e:
                print(f"⚠️ Warning: sequence sync skipped for {t}: {e}")

if __name__ == "__main__":
    asyncio.run(seed_partner_data())

