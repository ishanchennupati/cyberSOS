"""Replaceable handoff boundary; current provider opens a verified portal only."""
from typing import Protocol
from app.schemas.reporting import ReviewedCasePacket
from app.services.reporting_mapping import LOGIN


class HandoffProvider(Protocol):
    def prepare(self,packet:ReviewedCasePacket)->dict: ...


class OfficialPortalHandoff:
    def prepare(self,packet:ReviewedCasePacket)->dict:
        return {'mode':'external_portal','destination':LOGIN,'source_id':'NCRP-LOGIN',
            'meaning':'Opening the official portal does not submit this packet.',
            'jurisdiction':packet.jurisdiction,'submission_supported':False}
