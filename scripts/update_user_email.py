import asyncio
from sqlalchemy import select, update
from app.db.session import engine
from app.models.user import User

async def update_user_email(old_email: str, new_email: str):
    print(f"Checking for user with email: {old_email}...")
    async with engine.begin() as conn:
        # 1. Check if the old email exists
        result = await conn.execute(select(User).where(User.email == old_email))
        user_with_old_email = result.fetchone()
        
        # 2. Check if the new email already exists
        result_new = await conn.execute(select(User).where(User.email == new_email))
        user_with_new_email = result_new.fetchone()
        
        if user_with_new_email:
            print(f"NOTICE: User with new email {new_email} already exists.")
            if user_with_old_email:
                print(f"WARNING: Both {old_email} and {new_email} exist. Cannot update without causing a conflict.")
                print("Manual intervention required to merge or delete one of the accounts.")
            else:
                print(f"User is already updated to {new_email}. No action needed.")
            return

        if user_with_old_email:
            print(f"User found with {old_email}. Updating to {new_email}...")
            # We also update user_name if it was set to the old email
            await conn.execute(
                update(User)
                .where(User.email == old_email)
                .values(email=new_email, user_name=new_email)
            )
            print("Update successful.")
        else:
            print(f"No user found with email: {old_email}. Is it already updated?")

if __name__ == "__main__":
    # Target email update
    OLD = "ahmednu@datharm.com"
    NEW = "ahmednu@texis.com"
    
    asyncio.run(update_user_email(OLD, NEW))
