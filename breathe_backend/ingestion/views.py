from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.files.base import ContentFile

from tenants.models import Tenant
from .models import DataIngestion
from emissions.models import EmissionRecord
from .parsers import parse_sap, parse_utility, parse_travel


class UploadView(APIView):
    """
    POST /api/upload/
    Accepts a CSV file + source_type + tenant_id
    Parses it and creates EmissionRecords
    """

    def post(self, request):
        file        = request.FILES.get('file')
        source_type = request.data.get('source_type')
        tenant_id   = request.data.get('tenant_id', 1)

        if not file or not source_type:
            return Response(
                {'error': 'file and source_type are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        tenant = Tenant.objects.get(id=tenant_id)
        content = file.read().decode('utf-8')

        # Create the ingestion event record
        ingestion = DataIngestion.objects.create(
            tenant=tenant,
            source_type=source_type,
            original_filename=file.name,
            status='PROCESSING',
        )
        ingestion.file.save(file.name, ContentFile(content.encode()))

        # Pick the right parser
        parsers = {
            'SAP':     parse_sap,
            'UTILITY': parse_utility,
            'TRAVEL':  parse_travel,
        }

        if source_type not in parsers:
            ingestion.status = 'FAILED'
            ingestion.error_message = f'Unknown source type: {source_type}'
            ingestion.save()
            return Response({'error': 'Invalid source_type'}, status=400)

        records, errors = parsers[source_type](content)

        # Save all parsed records to the database
        created = []
        for rec in records:
            er = EmissionRecord.objects.create(
                tenant=tenant,
                ingestion=ingestion,
                source_row_id=rec['source_row_id'],
                scope=rec['scope'],
                category=rec['category'],
                raw_quantity=rec['raw_quantity'],
                raw_unit=rec['raw_unit'],
                raw_data=rec['raw_data'],
                normalized_quantity=rec['normalized_quantity'],
                normalized_unit=rec['normalized_unit'],
                emission_factor_used=rec['emission_factor_used'],
                emission_factor_source=rec['emission_factor_source'],
                period_start=rec['period_start'],
                period_end=rec['period_end'],
                facility_name=rec['facility_name'],
                country=rec['country'],
                description=rec['description'],
                status='PENDING',
            )
            created.append(er.id)

        # Update ingestion status
        ingestion.status = 'COMPLETED'
        ingestion.row_count = len(records)
        ingestion.error_count = len(errors)
        ingestion.save()

        return Response({
            'ingestion_id':   ingestion.id,
            'records_created': len(created),
            'errors':          errors,
            'status':          'COMPLETED',
        })