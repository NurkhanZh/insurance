
from pydantic import BaseModel


class EurasiaOsgpoConfig(BaseModel):
    allow_otp: bool = True
    allow_bmg: bool = True
    insurance: str = 'eurasia'
