from typing import Any, Final

AUDIT_EXAMPLE: Final[dict[str, Any]] = {
    "source_name": "SEACE_PENTAHO_CDA_RUC",
    "query_parameter": "20607524476",
    "duration_ms": 779,
    "status": "SUCCESS",
    "details": None,
    "executed_at_utc": "2026-11-10T14:49:46.322370Z",
}

SUNAT_EXAMPLE: Final[dict[str, Any]] = {
    "tax_id": "20607524476",
    "taxpayer_type": "EMPRESA INDIVIDUAL DE RESP. LTDA",
    "commercial_name": "INVERSIONES HUAYNA DEL PERU",
    "registration_date": "2021-02-24",
    "activity_start_date": "2021-03-15",
    "status": "BAJA DE OFICIO",
    "condition": "HABIDO",
    "tax_alert": None,
    "fiscal_address": "CAL.VILLA LA RINCONADA LOTE. H-1 APV. VILLA LA RINCONADA CUSCO - CUSCO - SAN JERONIMO",
    "economic_activities": ["Principal - 4630 - VENTA AL POR MAYOR DE ALIMENTOS, BEBIDAS Y TABACO"],
    "electronic_issuance": "FACTURA PORTAL DESDE 27/05/2021",
    "legal_representatives": [
        {
            "document_type": "DNI",
            "document_number": "44900952",
            "full_name": "RUIZ AUCCAPIÑA RONALD",
            "role": "TITULAR-GERENTE",
            "start_date": "2021-02-08",
        }
    ],
    "branch_offices": [
        {
            "code": "0004",
            "establishment_type": "LO. L. COMERCIAL",
            "address": "LOTE. 105 GRU. MERCADO MAYORISTA FERIAL DE PRODUCTORES OTR. STAND 105 CUSCO - CUSCO - SAN JERONIMO",
            "economic_activity": "4630",
        }
    ],
}

SEACE_RECORD_EXAMPLE: Final[dict[str, Any]] = {
    "ruc": "20607524476",
    "validities": [
        {
            "chapter": "Proveedor de Bienes",
            "status": "ACTIVE",
            "start_date": "2021-03-25",
            "end_date": None,
            "department": "CUSCO",
        }
    ],
    "shareholders": [
        {
            "relationship_type": "ACCIONISTA",
            "document_number": "44900952",
            "full_name": "RUIZ AUCCAPIÑA RONALD",
            "share_percentage": 100.0,
        }
    ],
    "awards": [
        {
            "fiscal_year": 2023,
            "modality": None,
            "contracting_entity": "MUNICIPALIDAD PROVINCIAL DE CALCA",
            "amount": 322592.71,
            "processes_count": 10,
        }
    ],
}

COMPANY_EXAMPLE: Final[dict[str, Any]] = {
    "ruc": "20607524476",
    "profile": {
        "document_number": "20607524476",
        "legal_name": "INVERSIONES Y SERVICIOS HUAYNA DEL PERU EMPRESA INDIVIDUAL DE RESPONSABILIDAD LIMITADA",
        "status": "BAJA DE OFICIO",
        "condition": "HABIDO",
        "address": "CAL. VILLA LA RINCONADA LOTE H-1 APV. VILLA LA RINCONADA",
        "ubigeo": "080104",
        "department": "CUSCO",
        "province": "CUSCO",
        "district": "SAN JERONIMO",
        "via_type": "CAL.",
        "via_name": "VILLA LA RINCONADA",
        "zone_type": "VILLA LA RINCONADA",
        "zone_code": "APV.",
        "number": None,
        "lot": "H-1",
        "apartment": None,
        "block": None,
        "kilometer": None,
    },
    "seace": SEACE_RECORD_EXAMPLE,
    "sunat": SUNAT_EXAMPLE,
    "rnp": {
        "ruc": "20607524476",
        "business_name": "INVERSIONES Y SERVICIOS HUAYNA DEL PERU EMPRESA INDIVIDUAL DE RESPONSABILIDAD LIMITADA",
        "registrations": [
            {
                "chapter": "BIENES",
                "provider_code": None,
                "payment_date": "2021-03-18",
                "procedure_number": "2021-18895585",
                "status": "APROBACION AUTOMATICA",
                "reason": "REQUISITOS CONFORME",
            }
        ],
    },
    "audit_entries": [AUDIT_EXAMPLE],
}

PERSON_EXAMPLE: Final[dict[str, Any]] = {
    "dni": "44900952",
    "profile": {
        "document_number": "44900952",
        "full_name": "RONALD RUIZ AUCCAPIÑA",
        "given_names": "RONALD",
        "first_surname": "RUIZ",
        "second_surname": "AUCCAPIÑA",
        "check_digit": None,
    },
    "seace": {
        "document_number": "44900952",
        "linked_providers": [
            {
                "presence": {
                    "ruc": "20607524476",
                    "business_name": "INVERSIONES Y SERVICIOS HUAYNA DEL PERU EMPRESA INDIVIDUAL DE RESPONSABILIDAD LIMITADA",
                    "condition": "VIGENTE",
                },
                "record": SEACE_RECORD_EXAMPLE,
            }
        ],
    },
    "sunat": {**SUNAT_EXAMPLE, "tax_id": "10449009521", "taxpayer_type": "PERSONA NATURAL SIN NEGOCIO"},
    "audit_entries": [{**AUDIT_EXAMPLE, "source_name": "SEACE_PENTAHO_CDA_DNI", "query_parameter": "44900952"}],
}
