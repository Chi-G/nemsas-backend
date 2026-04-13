from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.incident import IncidentChannel, IncidentStatus, EmergencyType
from src.schemas.incident import IncidentCreate
from src.services.incident import incident_service
from src.services.user import user_service
import re
from typing import Optional, Dict

class USSDService:
    @staticmethod
    async def handle_ussd_callback(db: AsyncSession, session_id: str, phone: str, text: str) -> str:
        """
        Logic for Africa's Talking USSD Menu (Criterion 75).
        text is cumulative, e.g., "1*Location*1"
        """
        parts = text.split("*") if text else []
        depth = len(parts)

        # 1. Start Session / Select Type
        if depth == 0 or (depth == 1 and not parts[0]):
            return (
                "CON Welcome to NEMSAS Emergency Response.\n"
                "Select Emergency Type:\n"
                "1. Medical\n"
                "2. Trauma\n"
                "3. Obstetric\n"
                "4. Pediatric\n"
                "5. Other"
            )

        # 2. Location Input
        if depth == 1:
            return f"CON Please enter your current location description (e.g. Area, Landmark):"

        # 3. Confirmation
        if depth == 2:
            emergency_type_map = {
                "1": "Medical", "2": "Trauma", "3": "Obstetric", "4": "Pediatric", "5": "Other"
            }
            etype = emergency_type_map.get(parts[0], "Other")
            location = parts[1]
            return (
                f"CON You reported a {etype} emergency at {location}.\n"
                "Confirm?\n"
                "1. Yes\n"
                "2. No"
            )

        # 4. Process Incident
        if depth == 3:
            if parts[2] == "1":
                emergency_type_map = {
                    "1": EmergencyType.MEDICAL, 
                    "2": EmergencyType.TRAUMA, 
                    "3": EmergencyType.OBSTETRIC, 
                    "4": EmergencyType.PEDIATRIC, 
                    "5": EmergencyType.OTHER
                }
                etype = emergency_type_map.get(parts[0], EmergencyType.OTHER)
                location = parts[1]
                
                # Get or create public user for the initiator
                user = await user_service.get_or_create_public_user(db, phone)
                
                incident_in = IncidentCreate(
                    location_label=location,
                    emergency_type=etype,
                    channel=IncidentChannel.USSD,
                    location_confirmed=False,
                    caller_phone=phone,
                    caller_name="USSD Reporter",
                    notes=f"Reported via USSD. Description: {location}",
                )
                
                incident = await incident_service.create(db, obj_in=incident_in, creator_id=user.id)
                return f"END Emergency reported! We are dispatching help. Ref: {incident.uuid[:8].upper()}"
            else:
                return "END Emergency report cancelled."

        return "END Invalid input. Please try again."

class SMSService:
    @staticmethod
    async def handle_sms_callback(db: AsyncSession, phone: str, text: str) -> str:
        """
        Logic for Africa's Talking SMS processing (Criterion 76).
        Expected format: EMERGENCY [TYPE] at [LOCATION]
        """
        # Case insensitive Regex to find type and location
        pattern = r"EMERGENCY\s+(MEDICAL|TRAUMA|OBSTETRIC|PEDIATRIC|OTHER)\s+AT\s+(.+)"
        match = re.search(pattern, text.strip(), re.IGNORECASE)
        
        if not match:
            # Send help message if format is invalid
            return (
                "Invalid format. Please use: EMERGENCY [TYPE] at [LOCATION].\n"
                "Types: Medical, Trauma, Obstetric, Pediatric, Other.\n"
                "Example: EMERGENCY MEDICAL at Lekki Toll Gate"
            )
            
        etype_str = match.group(1).capitalize()
        location = match.group(2).strip()
        
        etype = EmergencyType.OTHER
        if etype_str == "Medical": etype = EmergencyType.MEDICAL
        elif etype_str == "Trauma": etype = EmergencyType.TRAUMA
        elif etype_str == "Obstetric": etype = EmergencyType.OBSTETRIC
        elif etype_str == "Pediatric": etype = EmergencyType.PEDIATRIC
        
        user = await user_service.get_or_create_public_user(db, phone)
        
        incident_in = IncidentCreate(
            location_label=location,
            emergency_type=etype,
            channel=IncidentChannel.SMS,
            location_confirmed=False,
            caller_phone=phone,
            caller_name="SMS Reporter",
            notes=f"Reported via SMS. Raw: {text}",
        )
        
        incident = await incident_service.create(db, obj_in=incident_in, creator_id=user.id)
        return f"Emergency reported! We are dispatching help. Ref: {incident.uuid[:8].upper()}"

class VoiceService:
    @staticmethod
    async def handle_voice_callback(db: AsyncSession, call_session_id: str, phone: str, is_active: str) -> str:
        """
        Logic for Africa's Talking Voice (Call) processing.
        isActive: 1 means call started, 0 means call ended.
        """
        if is_active == "1":
            # Call started - Create incident
            user = await user_service.get_or_create_public_user(db, phone)
            
            incident_in = IncidentCreate(
                location_label="Unknown (Voice Call)",
                emergency_type=EmergencyType.OTHER,
                channel=IncidentChannel.CALL,
                location_confirmed=False,
                caller_phone=phone,
                caller_name="Voice Caller",
                notes=f"Reported via Voice Call. Session: {call_session_id}",
            )
            
            incident = await incident_service.create(db, obj_in=incident_in, creator_id=user.id)
            
            # Return XML response
            return (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Response>'
                f'<Say voice="en-US-Standard-C">Welcome to NEMSAS Emergency Service. Your request has been logged. Reference: {incident.uuid[:8].upper()}. Please stay on the line to speak with a dispatcher.</Say>'
                '</Response>'
            )
        
        return '<?xml version="1.0" encoding="UTF-8"?><Response><Reject/></Response>'

ussd_service = USSDService()
sms_service = SMSService()
voice_service = VoiceService()
