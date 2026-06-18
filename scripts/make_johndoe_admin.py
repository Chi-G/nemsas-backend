import asyncio
from app.db.session import SessionLocal
from app.models.user import User
from app.partners.models import PartnerUser
from sqlalchemy.future import select

async def make_johndoe_admin():
    async with SessionLocal() as db:
        # Get Johndoe from partner users
        result = await db.execute(select(PartnerUser).where(PartnerUser.email == 'chijindu.nwokeohuru@gmail.com'))
        partner_john = result.scalar_one_or_none()
        
        if not partner_john:
            print("John Doe partner not found!")
            return
            
        # Check if already exists in users table
        result = await db.execute(select(User).where(User.email == partner_john.email))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print("John Doe already exists in the users table.")
            # Ensure he's an admin
            existing_user.user_type = "SUPERADMINISTRATOR"
            await db.commit()
            print("Set existing user to SUPERADMINISTRATOR.")
            return
            
        # Create mirror user in the main users table
        new_admin = User(
            first_name=partner_john.first_name,
            last_name=partner_john.last_name,
            middle_name=partner_john.middle_name,
            user_name="johndoe_admin",
            email=partner_john.email,
            hashed_password=partner_john.hashed_password,
            user_type="SUPERADMINISTRATOR",
            is_active=True
        )
        db.add(new_admin)
        await db.commit()
        print("John Doe has been added to the main users table as a SUPERADMINISTRATOR!")

if __name__ == "__main__":
    asyncio.run(make_johndoe_admin())
