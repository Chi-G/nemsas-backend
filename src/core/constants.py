from src.db.models.incident import IncidentStatus

# Criterion 63: Strict Incident Status Transitions
# Format: Current Status -> List of Allowed Next Statuses
INCIDENT_TRANSITION_MAP = {
    IncidentStatus.CREATED: [IncidentStatus.DISPATCHED, IncidentStatus.CLOSED], # Can close directly if false alarm
    IncidentStatus.DISPATCHED: [IncidentStatus.ACCEPTED, IncidentStatus.CREATED], # Can go back if crew rejects/unavailable
    IncidentStatus.ACCEPTED: [IncidentStatus.EN_ROUTE],
    IncidentStatus.EN_ROUTE: [IncidentStatus.AT_SCENE],
    IncidentStatus.AT_SCENE: [IncidentStatus.PATIENT_LOADED, IncidentStatus.COMPLETED], # Completed if no patient transport needed
    IncidentStatus.PATIENT_LOADED: [IncidentStatus.EN_ROUTE_TO_ETC],
    IncidentStatus.EN_ROUTE_TO_ETC: [IncidentStatus.ARRIVED_AT_ETC],
    IncidentStatus.ARRIVED_AT_ETC: [IncidentStatus.COMPLETED],
    IncidentStatus.COMPLETED: [IncidentStatus.CLOSED],
    IncidentStatus.CLOSED: [], # Terminal state
}
