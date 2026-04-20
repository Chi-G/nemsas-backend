"""Create core incident, ambulance, and claim tables

Revision ID: acaca90604cf
Revises: 302d96555d23
Create Date: 2026-04-14 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'acaca90604cf'
down_revision: Union[str, Sequence[str], None] = '302d96555d23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Create incident, ambulance, claim tables."""
    
    # Create Incidents table
    op.create_table('incidents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=36), nullable=False),
        sa.Column('location_label', sa.String(length=255), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('state_id', sa.Integer(), nullable=False),
        sa.Column('lga_id', sa.Integer(), nullable=False),
        sa.Column('caller_name', sa.String(length=255), nullable=True),
        sa.Column('caller_phone', sa.String(length=20), nullable=True),
        sa.Column('emergency_type', sa.Enum('MEDICAL', 'TRAUMA', 'OBSTETRIC', 'PEDIATRIC', 'OTHER', name='emergencytype'), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=True),
        sa.Column('patient_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('notes', sa.String(length=1000), nullable=True),
        sa.Column('status', sa.Enum('CREATED', 'DISPATCHED', 'ACCEPTED', 'EN_ROUTE', 'AT_SCENE', 'PATIENT_LOADED', 'EN_ROUTE_TO_ETC', 'ARRIVED_AT_ETC', 'COMPLETED', 'CLOSED', name='incidentstatus'), nullable=False, server_default='CREATED'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['lga_id'], ['lgas.id'], ),
        sa.ForeignKeyConstraint(['state_id'], ['states.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    op.create_index(op.f('ix_incidents_uuid'), 'incidents', ['uuid'], unique=True)
    op.create_index(op.f('ix_incidents_state_id'), 'incidents', ['state_id'], unique=False)
    op.create_index(op.f('ix_incidents_lga_id'), 'incidents', ['lga_id'], unique=False)

    # Create IncidentStatusHistory table
    op.create_table('incident_status_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('incident_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('CREATED', 'DISPATCHED', 'ACCEPTED', 'EN_ROUTE', 'AT_SCENE', 'PATIENT_LOADED', 'EN_ROUTE_TO_ETC', 'ARRIVED_AT_ETC', 'COMPLETED', 'CLOSED', name='incidentstatus'), nullable=False),
        sa.Column('changed_at', sa.DateTime(), nullable=False),
        sa.Column('changed_by_id', sa.Integer(), nullable=False),
        sa.Column('notes', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['changed_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create QAFinding table
    op.create_table('qa_findings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('incident_id', sa.Integer(), nullable=False),
        sa.Column('compliance_rating', sa.String(length=50), nullable=False),
        sa.Column('findings_text', sa.String(length=1000), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('qa_officer_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ),
        sa.ForeignKeyConstraint(['qa_officer_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create Ambulances table
    op.create_table('ambulances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plate_number', sa.String(length=20), nullable=False),
        sa.Column('make_model', sa.String(length=255), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('accreditation_type', sa.Enum('BLS', 'ALS', name='accreditationtype'), nullable=False),
        sa.Column('fuel_type', sa.String(length=50), nullable=True),
        sa.Column('capacity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.Enum('ACTIVE', 'UNDER_MAINTENANCE', 'OFFLINE', 'DECOMMISSIONED', 'ON_DUTY', name='ambulancestatus'), nullable=False, server_default='ACTIVE'),
        sa.Column('is_paused', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('last_latitude', sa.Float(), nullable=True),
        sa.Column('last_longitude', sa.Float(), nullable=True),
        sa.Column('state_id', sa.Integer(), nullable=False),
        sa.Column('lga_id', sa.Integer(), nullable=False),
        sa.Column('partner_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['lga_id'], ['lgas.id'], ),
        sa.ForeignKeyConstraint(['partner_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['state_id'], ['states.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plate_number')
    )
    op.create_index(op.f('ix_ambulances_plate_number'), 'ambulances', ['plate_number'], unique=True)
    op.create_index(op.f('ix_ambulances_state_id'), 'ambulances', ['state_id'], unique=False)
    op.create_index(op.f('ix_ambulances_lga_id'), 'ambulances', ['lga_id'], unique=False)
    op.create_index(op.f('ix_ambulances_partner_id'), 'ambulances', ['partner_id'], unique=False)

    # Create Dispatches table
    op.create_table('dispatches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('incident_id', sa.Integer(), nullable=False),
        sa.Column('ambulance_id', sa.Integer(), nullable=False),
        sa.Column('crew_id', sa.Integer(), nullable=False),
        sa.Column('dispatch_timestamp', sa.DateTime(), nullable=False),
        sa.Column('accepted_timestamp', sa.DateTime(), nullable=True),
        sa.Column('completed_timestamp', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['ambulance_id'], ['ambulances.id'], ),
        sa.ForeignKeyConstraint(['crew_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dispatches_incident_id'), 'dispatches', ['incident_id'], unique=False)
    op.create_index(op.f('ix_dispatches_ambulance_id'), 'dispatches', ['ambulance_id'], unique=False)

    # Create GPSHistory table
    op.create_table('gps_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ambulance_id', sa.Integer(), nullable=False),
        sa.Column('incident_id', sa.Integer(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('is_paused', sa.Boolean(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['ambulance_id'], ['ambulances.id'], ),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create RunSheets table
    op.create_table('run_sheets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('incident_id', sa.Integer(), nullable=False),
        sa.Column('patient_data', sa.JSON(), nullable=True),
        sa.Column('drugs_administered', sa.JSON(), nullable=True),
        sa.Column('crew_signature', sa.String(length=255), nullable=True),
        sa.Column('crew_signed_at', sa.DateTime(), nullable=True),
        sa.Column('crew_id', sa.Integer(), nullable=True),
        sa.Column('etc_signature', sa.String(length=255), nullable=True),
        sa.Column('etc_signed_at', sa.DateTime(), nullable=True),
        sa.Column('etc_staff_id', sa.Integer(), nullable=True),
        sa.Column('is_locked', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['crew_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['etc_staff_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('incident_id')
    )

    # Create ETCIntakes table
    op.create_table('etc_intakes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('incident_id', sa.Integer(), nullable=False),
        sa.Column('etc_facility_id', sa.Integer(), nullable=False),
        sa.Column('arrival_time', sa.DateTime(), nullable=False),
        sa.Column('initial_assessment', sa.String(length=1000), nullable=False),
        sa.Column('triage_category', sa.String(length=50), nullable=False),
        sa.Column('interventions', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['etc_facility_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('incident_id')
    )

    # Create Claims table
    op.create_table('claims',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('incident_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('claim_type', sa.Enum('AMBULANCE', 'ETC', name='claimtype'), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('distance_km', sa.Float(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', 'PAID', name='claimstatus'), nullable=False, server_default='PENDING'),
        sa.Column('rejection_reason', sa.String(length=255), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('processed_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ),
        sa.ForeignKeyConstraint(['processed_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create Partners table
    op.create_table('partners',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('organisation_name', sa.String(length=255), nullable=False),
        sa.Column('contact_person', sa.String(length=255), nullable=False),
        sa.Column('contact_phone', sa.String(length=20), nullable=False),
        sa.Column('address', sa.String(length=500), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    # Create Pledges table
    op.create_table('pledges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('partner_id', sa.Integer(), nullable=False),
        sa.Column('ambulance_count', sa.Integer(), nullable=False),
        sa.Column('target_state_id', sa.Integer(), nullable=True),
        sa.Column('target_lga_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'IN_PROGRESS', 'PARTIALLY_FULFILLED', 'FULFILLED', 'REJECTED', name='pledgestatus'), nullable=False, server_default='PENDING'),
        sa.Column('fulfilled_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create Facilities table
    op.create_table('facilities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('facility_type', sa.String(length=100), nullable=False),
        sa.Column('address', sa.String(length=500), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('state_id', sa.Integer(), nullable=False),
        sa.Column('lga_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['lga_id'], ['lgas.id'], ),
        sa.ForeignKeyConstraint(['state_id'], ['states.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_facilities_name'), 'facilities', ['name'], unique=True)
    op.create_index(op.f('ix_facilities_state_id'), 'facilities', ['state_id'], unique=False)
    op.create_index(op.f('ix_facilities_lga_id'), 'facilities', ['lga_id'], unique=False)

    # Create FacilityRequests table
    op.create_table('facility_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('partner_id', sa.Integer(), nullable=False),
        sa.Column('facility_name', sa.String(length=255), nullable=False),
        sa.Column('facility_type', sa.String(length=100), nullable=False),
        sa.Column('address', sa.String(length=500), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('state_id', sa.Integer(), nullable=False),
        sa.Column('lga_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='facilityrequestatus'), nullable=False, server_default='PENDING'),
        sa.Column('rejection_reason', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['lga_id'], ['lgas.id'], ),
        sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ),
        sa.ForeignKeyConstraint(['state_id'], ['states.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_facility_requests_state_id'), 'facility_requests', ['state_id'], unique=False)
    op.create_index(op.f('ix_facility_requests_lga_id'), 'facility_requests', ['lga_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_facility_requests_lga_id'), table_name='facility_requests')
    op.drop_index(op.f('ix_facility_requests_state_id'), table_name='facility_requests')
    op.drop_table('facility_requests')
    op.drop_index(op.f('ix_facilities_lga_id'), table_name='facilities')
    op.drop_index(op.f('ix_facilities_state_id'), table_name='facilities')
    op.drop_index(op.f('ix_facilities_name'), table_name='facilities')
    op.drop_table('facilities')
    op.drop_table('pledges')
    op.drop_table('partners')
    op.drop_table('claims')
    op.drop_table('etc_intakes')
    op.drop_table('run_sheets')
    op.drop_table('gps_history')
    op.drop_index(op.f('ix_dispatches_ambulance_id'), table_name='dispatches')
    op.drop_index(op.f('ix_dispatches_incident_id'), table_name='dispatches')
    op.drop_table('dispatches')
    op.drop_index(op.f('ix_ambulances_partner_id'), table_name='ambulances')
    op.drop_index(op.f('ix_ambulances_lga_id'), table_name='ambulances')
    op.drop_index(op.f('ix_ambulances_state_id'), table_name='ambulances')
    op.drop_index(op.f('ix_ambulances_plate_number'), table_name='ambulances')
    op.drop_table('ambulances')
    op.drop_table('qa_findings')
    op.drop_table('incident_status_history')
    op.drop_index(op.f('ix_incidents_lga_id'), table_name='incidents')
    op.drop_index(op.f('ix_incidents_state_id'), table_name='incidents')
    op.drop_index(op.f('ix_incidents_uuid'), table_name='incidents')
    op.drop_table('incidents')
