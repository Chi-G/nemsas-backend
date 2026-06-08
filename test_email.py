import asyncio
from app.core.email import send_verification_email

def test():
    print("Testing email send...")
    send_verification_email("testpartner123@mailinator.com", "Test Partner", "123456")
    print("Done testing.")

if __name__ == "__main__":
    test()
