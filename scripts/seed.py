import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.db.base import SessionLocal, engine, Base
from src.db.models.user import Role, Permission, User
from src.db.models.reference import State, LGA, Drug
from src.core.security import get_password_hash
from src.core.rbac import ROLE_PERMISSIONS, Permission as RbacPermission

async def seed_data():
    # 0. Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with SessionLocal() as db:
        # 1. Seed Roles (Idempotent)
        roles_data = [
            {"name": "NEMSAS Admin", "description": "Full system access (Super Admin)"},
            {"name": "SEMSAS Admin", "description": "State level administration and oversight"},
            {"name": "Dispatcher", "description": "Emergency call handling and ambulance assignment"},
            {"name": "Ambulance Crew", "description": "Field paramedics and transport crew"},
            {"name": "Emergency Transport Provider", "description": "Fleet owners and managers"},
            {"name": "ETC Staff", "description": "Emergency Treatment Centre medical personnel"},
            {"name": "Claims Staff", "description": "Financial claim review and approval"},
            {"name": "QA Officer", "description": "Quality assurance and operational audit"},
            {"name": "Accounts Staff", "description": "Financial and operational audit (Read-only)"},
            {"name": "Partner", "description": "Private/Public contributors and asset owners"},
            {"name": "View-Only User", "description": "Analytics and reports read-only access"},
        ]
        
        # 1. Seed Roles (Idempotent)
        for r_data in roles_data:
            stmt = select(Role).where(Role.name == r_data["name"])
            existing = await db.execute(stmt)
            role = existing.scalar_one_or_none()
            if not role:
                role = Role(**r_data)
                db.add(role)
        await db.flush()
            
        # 1.1 Seed Permissions (Idempotent)
        all_perms = {}
        for perm_enum in RbacPermission:
            stmt = select(Permission).where(Permission.name == perm_enum.value)
            existing = await db.execute(stmt)
            perm_obj = existing.scalar_one_or_none()
            if not perm_obj:
                perm_obj = Permission(name=perm_enum.value, description=f"Permission for {perm_enum.value}")
                db.add(perm_obj)
                await db.flush()
            all_perms[perm_enum.value] = perm_obj

        # 1.2 Associate Roles with Permissions
        # Re-fetch roles with selectinload to avoid lazy loading
        stmt = select(Role).options(selectinload(Role.permissions))
        existing_roles = await db.execute(stmt)
        roles = {r.name: r for r in existing_roles.scalars().all()}

        for role_name, perm_set in ROLE_PERMISSIONS.items():
            role_obj = roles.get(role_name)
            if role_obj:
                role_obj.permissions = [all_perms[p.value] for p in perm_set if p.value in all_perms]
        
        await db.commit()
        # Start new transaction for the rest
        await db.begin()
        states_names = [
            "Abia", "Adamawa", "Akwa Ibom", "Anambra", "Bauchi", "Bayelsa", "Benue", "Borno", 
            "Cross River", "Delta", "Ebonyi", "Edo", "Ekiti", "Enugu", "FCT", "Gombe", 
            "Imo", "Jigawa", "Kaduna", "Kano", "Katsina", "Kebbi", "Kogi", "Kwara", 
            "Lagos", "Nasarawa", "Niger", "Ogun", "Ondo", "Osun", "Oyo", "Plateau", 
            "Rivers", "Sokoto", "Taraba", "Yobe", "Zamfara"
        ]
        
        states = {}
        for s_name in states_names:
            stmt = select(State).where(State.name == s_name)
            existing = await db.execute(stmt)
            state = existing.scalar_one_or_none()
            if not state:
                state = State(name=s_name, population=3000000)
                db.add(state)
                await db.flush()
            states[s_name] = state
            
        # 3. Seed Sample LGAs (Focus on FCT for demo - Idempotent)
        fct_lgas = ["Abuja Municipal", "Bwari", "Gwagwalada", "Kuje", "Kwali", "Abaji"]
        for lga_name in fct_lgas:
            stmt = select(LGA).where(LGA.name == lga_name, LGA.state_id == states["FCT"].id)
            existing = await db.execute(stmt)
            if not existing.scalar_one_or_none():
                lga = LGA(state_id=states["FCT"].id, name=lga_name)
                db.add(lga)
            
        # 4. Seed NHIA Approved Drug List (Idempotent)
        drugs = [
            {"name": "Adrenaline", "dosage_form": "Injection 1mg/ml"},
            {"name": "Atropine", "dosage_form": "Injection 0.6mg/ml"},
            {"name": "Amiodarone", "dosage_form": "Injection 50mg/ml"},
            {"name": "Dextrose 50%", "dosage_form": "Injection 50ml"},
            {"name": "Salbutamol", "dosage_form": "Nebuliser Solution"},
            {"name": "Hydrocortisone", "dosage_form": "Injection 100mg"},
            {"name": "Diazepam", "dosage_form": "Injection 5mg/ml"},
            {"name": "Morphine", "dosage_form": "Injection 10mg/ml"},
            {"name": "Naloxone", "dosage_form": "Injection 0.4mg/ml"},
            {"name": "Oxygen", "dosage_form": "Medical Gas"},
            {"name": "Sodium Chloride 0.9%", "dosage_form": "IV Infusion 500ml"},
            {"name": "Hartmann's Solution", "dosage_form": "IV Infusion 500ml"},
        ]
        for d_data in drugs:
            stmt = select(Drug).where(Drug.name == d_data["name"])
            existing = await db.execute(stmt)
            if not existing.scalar_one_or_none():
                drug = Drug(**d_data)
                db.add(drug)
            
        # 5. Create Default Admin User (Idempotent)
        admin_email = "admin@nemsas.gov.ng"
        stmt = select(User).where(User.email == admin_email)
        existing_admin = await db.execute(stmt)
        admin_obj = existing_admin.scalar_one_or_none()
        
        if not admin_obj:
            print(f"Creating default admin user: {admin_email}...")
            admin_user = User(
                email=admin_email,
                name="System Administrator",
                hashed_password=get_password_hash("chibuike4u"),
                is_active=True,
                role_id=roles["NEMSAS Admin"].id
            )
            db.add(admin_user)
        else:
            print(f"Admin user {admin_email} already exists. skipping creation.")
        
        await db.commit()
        print("✅ Database successfully initialized and seeded with National Data (Idempotently)!")

if __name__ == "__main__":
    asyncio.run(seed_data())
