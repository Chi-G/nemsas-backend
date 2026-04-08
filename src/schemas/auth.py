from pydantic import BaseModel, EmailStr, Field

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8)

class ActivateAccountRequest(BaseModel):
    token: str
    password: str = Field(..., min_length=8)

class ResendActivationRequest(BaseModel):
    email: EmailStr

class Verify2FARequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)

class MessageResponse(BaseModel):
    message: str
