import logging

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    async def send_dispatch_notification(crew_id: int, incident_id: int, ambulance_id: int):
        """
        Stub for pushing notifications to the ambulance crew.
        In a real scenario, this would integrate with Firebase Cloud Messaging (FCM).
        """
        logger.info(f"NOTIFICATION: Dispatch pushed to Crew {crew_id} for Incident {incident_id} using Ambulance {ambulance_id}")
        # In the future: await fcm_service.send_to_user(crew_id, message_data)
        return True

    @staticmethod
    async def send_status_update_notification(recipient_id: int, incident_id: int, status: str):
        """
        Stub for notifyting various stakeholders about status changes.
        """
        logger.info(f"NOTIFICATION: Status of Incident {incident_id} changed to {status}. Notifying User {recipient_id}")
        return True

    @staticmethod
    async def send_claim_status_notification(recipient_id: int, claim_id: int, status: str):
        """
        Notify the submitting party about claim status changes.
        """
        logger.info(f"NOTIFICATION: Claim {claim_id} status changed to {status}. Notifying User {recipient_id}")
        return True

notification_service = NotificationService()
