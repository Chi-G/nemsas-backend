import asyncio
from sqlalchemy import select, update
from app.db.session import engine
from app.models.user import User

async def update_user_email(old_email: str, new_email: str):
    async with engine.begin() as conn:
        # Check if user exists
        result = await conn.execute(select(User).where(User.email == old_email))
        user = result.fetchone()
        
        if user:
            print(f"User found. Updating email from {old_email} to {new_email}...")
            await conn.execute(
                update(User)
                .where(User.email == old_email)
                .values(email=new_email)
            )
            print("Update successful.")
        else:
            print(f"No user found with email: {old_email}")

if __name__ == "__main__":
    old_email = "ahmednu@datharm.com"
    new_email = "ahmednu@texis.com"
    asyncio.run(update_user_email(old_email, new_email))
