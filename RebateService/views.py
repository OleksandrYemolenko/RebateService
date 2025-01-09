from datetime import datetime

from django.db.models import Sum
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Transaction, RebateClaim
from .serializers import (
    RebateProgramSerializer,
    TransactionSerializer,
)
from .specifications import MinAmountSpecification, TransactionDateRangeSpecification, AndSpecification


@api_view(['GET'])
def health(request):
    return Response("Healthy", status=status.HTTP_200_OK)


@api_view(['POST'])
def create_rebate_program(request):
    """Create a new rebate program"""
    serializer = RebateProgramSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def create_transaction(request):
    """Create a new transaction"""
    serializer = TransactionSerializer(data=request.data)

    if serializer.is_valid():
        rebate_program = serializer.validated_data.get('rebate_program')
        transaction = serializer.save()

        specs = []
        if 'minimal_count' in rebate_program.eligibility_criteria:
            specs.append(MinAmountSpecification(rebate_program.eligibility_criteria['minimal_count']))

        print(rebate_program.eligibility_criteria['minimal_count'])

        specs.append(TransactionDateRangeSpecification(
            rebate_program.start_date,
            rebate_program.end_date
        ))

        combined_spec = AndSpecification(*specs)

        # Check if transaction date is within rebate program's date range
        if not combined_spec.is_satisfied_by(transaction):
            transaction.eligibility_status = "not_eligible"
        else:
            transaction.eligibility_status = "eligible"

        transaction.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def calculate_rebate(request, transaction_id):
    """Calculate rebate for a given transaction"""
    try:
        transaction = Transaction.objects.get(pk=transaction_id)
    except Transaction.DoesNotExist:
        return Response(
            {'error': 'Transaction not found.'}, status=status.HTTP_404_NOT_FOUND
        )

    if transaction.eligibility_status == "not_eligible":
        return Response(
            {'Transaction is not eligible for rebate.'}, status=status.HTTP_200_OK
        )

    rebate_program = transaction.rebate_program
    if rebate_program:
        rebate_amount = (transaction.amount * rebate_program.rebate_percentage) / 100
        return Response(
            {'rebate_amount': rebate_amount},
            status=status.HTTP_200_OK,
        )
    return Response(
        {'Transaction is not eligible for rebate.'}, status=status.HTTP_200_OK
    )


@api_view(['POST'])
def claim_rebate(request):
    """Claim rebate for a transaction"""
    transaction_list = Transaction.objects.filter(eligibility_status="eligible").exclude(rebate_claims__isnull=False)

    for transaction in transaction_list:
        rebate_claim = RebateClaim()
        rebate_claim.transaction = transaction
        rebate_claim.claim_amount = (transaction.amount * transaction.get_rebate_percentage()) / 100
        rebate_claim.claim_date = datetime.now()
        rebate_claim.save()

    return Response(status=status.HTTP_200_OK)


@api_view(['GET'])
def get_report(request):
    """Get a summary of total rebate claims and the amount approved for a given period"""
    period_start = request.query_params.get('period_start')
    period_end = request.query_params.get('period_end')

    try:
        period_start = datetime.strptime(period_start, '%Y-%m-%d')
        period_end = datetime.strptime(period_end, '%Y-%m-%d')
    except (TypeError, ValueError):
        return Response(
            {'error': 'Invalid date format. Use YYYY-MM-DD.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    claims = RebateClaim.objects.filter(
        claim_date__range=(period_start, period_end)
    )
    total_claims = claims.count()
    approved_amount = claims.filter(claim_status='approved').aggregate(
        total=Sum('claim_amount')
    )['total'] or 0

    return Response(
        {
            'total_claims': total_claims,
            'approved_amount': approved_amount,
        },
        status=status.HTTP_200_OK,
    )
