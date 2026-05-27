from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from emissions.models import EmissionRecord
from .models import AuditLog


class RecordListView(APIView):
    """GET /api/records/ — list all emission records with optional filters"""

    def get(self, request):
        qs = EmissionRecord.objects.all()

        # Filters
        status_filter = request.query_params.get('status')
        scope_filter  = request.query_params.get('scope')
        source_filter = request.query_params.get('source_type')

        if status_filter:
            qs = qs.filter(status=status_filter)
        if scope_filter:
            qs = qs.filter(scope=scope_filter)
        if source_filter:
            qs = qs.filter(ingestion__source_type=source_filter)

        data = []
        for r in qs:
            data.append({
                'id':                   r.id,
                'scope':                r.scope,
                'category':             r.category,
                'description':          r.description,
                'raw_quantity':         float(r.raw_quantity),
                'raw_unit':             r.raw_unit,
                'normalized_quantity':  float(r.normalized_quantity),
                'normalized_unit':      r.normalized_unit,
                'emission_factor_source': r.emission_factor_source,
                'period_start':         r.period_start.isoformat(),
                'period_end':           r.period_end.isoformat(),
                'facility_name':        r.facility_name,
                'status':               r.status,
                'flag_reason':          r.flag_reason,
                'source_type':          r.ingestion.source_type,
                'ingestion_id':         r.ingestion.id,
                'created_at':           r.created_at.isoformat(),
            })

        return Response({'records': data, 'total': len(data)})


class RecordActionView(APIView):
    """PATCH /api/records/<id>/action/ — approve, flag, or lock a record"""

    def patch(self, request, pk):
        try:
            record = EmissionRecord.objects.get(id=pk)
        except EmissionRecord.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        action     = request.data.get('action')   # 'approve', 'flag', 'lock'
        flag_reason = request.data.get('flag_reason', '')

        before = {'status': record.status}

        if action == 'approve':
            record.status = 'APPROVED'
            record.reviewed_at = timezone.now()
            audit_action = 'APPROVED'
        elif action == 'flag':
            record.status = 'FLAGGED'
            record.flag_reason = flag_reason
            audit_action = 'FLAGGED'
        elif action == 'lock':
            if record.status != 'APPROVED':
                return Response({'error': 'Only approved records can be locked'}, status=400)
            record.status = 'LOCKED'
            record.locked_at = timezone.now()
            audit_action = 'LOCKED'
        else:
            return Response({'error': 'Invalid action'}, status=400)

        record.save()

        # Write to audit log — immutable
        AuditLog.objects.create(
            record=record,
            action=audit_action,
            note=flag_reason,
            before_state=before,
            after_state={'status': record.status},
        )

        return Response({'id': record.id, 'status': record.status})


class StatsView(APIView):
    """GET /api/stats/ — summary numbers for the dashboard"""

    def get(self, request):
        records = EmissionRecord.objects.all()

        total_co2e = sum(float(r.normalized_quantity) for r in records)

        by_scope = {}
        for r in records:
            by_scope[r.scope] = by_scope.get(r.scope, 0) + float(r.normalized_quantity)

        by_status = {}
        for r in records:
            by_status[r.status] = by_status.get(r.status, 0) + 1

        return Response({
            'total_records': records.count(),
            'total_co2e_kg': round(total_co2e, 2),
            'by_scope':      by_scope,
            'by_status':     by_status,
        })