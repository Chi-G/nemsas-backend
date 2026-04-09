from enum import Enum
from typing import Dict, List, Set

class Permission(str, Enum):
    # User Management
    USER_READ = "user:read"
    USER_MANAGE = "user:manage"
    
    # Incident Management
    INCIDENT_READ = "incident:read"
    INCIDENT_CREATE = "incident:create"
    INCIDENT_MANAGE = "incident:manage"
    INCIDENT_CLOSE = "incident:close"
    
    # Ambulance & Dispatch
    AMBULANCE_READ = "ambulance:read"
    AMBULANCE_MANAGE = "ambulance:manage"
    DISPATCH_READ = "dispatch:read"
    DISPATCH_CREATE = "dispatch:create"
    DISPATCH_MANAGE = "dispatch:manage"
    
    # Run Sheets & Intake
    RUNSHEET_READ = "runsheet:read"
    RUNSHEET_WRITE = "runsheet:write"
    RUNSHEET_SIGN = "runsheet:sign"
    
    # ETC Operations
    ETC_READ = "etc:read"
    ETC_INTAKE = "etc:intake"
    ETC_SIGN = "etc:sign"
    
    # Claims
    CLAIM_READ = "claim:read"
    CLAIM_CREATE = "claim:create"
    CLAIM_APPROVE = "claim:approve"
    CLAIM_REJECT = "claim:reject"
    
    # QA & Audit
    QA_READ = "qa:read"
    QA_ASSESS = "qa:assess"
    
    # Partner & Fleet
    PARTNER_READ = "partner:read"
    PARTNER_MANAGE = "partner:manage"
    FLEET_READ = "fleet:read"
    FLEET_MANAGE = "fleet:manage"
    
    # Reference Data
    REFERENCE_READ = "reference:read"
    REFERENCE_MANAGE = "reference:manage"

class RoleName(str, Enum):
    NEMSAS_ADMIN = "NEMSAS Admin"
    SEMSAS_ADMIN = "SEMSAS Admin"
    DISPATCHER = "Dispatcher"
    AMBULANCE_CREW = "Ambulance Crew"
    ETP = "Emergency Transport Provider"
    ETC_STAFF = "ETC Staff"
    CLAIMS_STAFF = "Claims Staff"
    QA_OFFICER = "QA Officer"
    PARTNER = "Partner"
    ACCOUNTS_STAFF = "Accounts Staff"
    VIEW_ONLY = "View-Only User"

# Role to Permission Mapping
ROLE_PERMISSIONS: Dict[str, Set[Permission]] = {
    RoleName.NEMSAS_ADMIN: set(Permission), # All permissions
    
    RoleName.SEMSAS_ADMIN: {
        Permission.USER_READ, Permission.INCIDENT_READ, Permission.INCIDENT_MANAGE,
        Permission.AMBULANCE_READ, Permission.DISPATCH_READ, Permission.RUNSHEET_READ,
        Permission.ETC_READ, Permission.CLAIM_READ, Permission.QA_READ,
        Permission.PARTNER_READ, Permission.FLEET_READ, Permission.REFERENCE_READ
    },
    
    RoleName.DISPATCHER: {
        Permission.INCIDENT_READ, Permission.INCIDENT_CREATE, Permission.INCIDENT_MANAGE,
        Permission.INCIDENT_CLOSE, Permission.AMBULANCE_READ, Permission.DISPATCH_READ,
        Permission.DISPATCH_CREATE, Permission.DISPATCH_MANAGE, Permission.RUNSHEET_READ
    },
    
    RoleName.AMBULANCE_CREW: {
        Permission.INCIDENT_READ, Permission.AMBULANCE_READ, Permission.DISPATCH_READ,
        Permission.RUNSHEET_READ, Permission.RUNSHEET_WRITE, Permission.RUNSHEET_SIGN,
        Permission.CLAIM_CREATE, Permission.CLAIM_READ
    },
    
    RoleName.ETC_STAFF: {
        Permission.INCIDENT_READ, Permission.RUNSHEET_READ, Permission.RUNSHEET_WRITE,
        Permission.ETC_READ, Permission.ETC_INTAKE, Permission.ETC_SIGN,
        Permission.CLAIM_CREATE, Permission.CLAIM_READ
    },
    
    RoleName.CLAIMS_STAFF: {
        Permission.CLAIM_READ, Permission.CLAIM_APPROVE, Permission.CLAIM_REJECT,
        Permission.INCIDENT_READ, Permission.RUNSHEET_READ
    },
    
    RoleName.QA_OFFICER: {
        Permission.QA_READ, Permission.QA_ASSESS, Permission.INCIDENT_READ, Permission.RUNSHEET_READ
    },
    
    RoleName.PARTNER: {
        Permission.PARTNER_READ, Permission.FLEET_READ, Permission.FLEET_MANAGE, Permission.CLAIM_READ
    },
    
    RoleName.ACCOUNTS_STAFF: {
        Permission.CLAIM_READ, Permission.INCIDENT_READ, Permission.REFERENCE_READ
    },
    
    RoleName.VIEW_ONLY: {
        Permission.INCIDENT_READ, Permission.AMBULANCE_READ, Permission.PARTNER_READ, 
        Permission.FLEET_READ, Permission.REFERENCE_READ
    }
}

READ_ONLY_ROLES = {RoleName.ACCOUNTS_STAFF, RoleName.VIEW_ONLY}

def is_read_only_role(role_name: str) -> bool:
    return role_name in READ_ONLY_ROLES
