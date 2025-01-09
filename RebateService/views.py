import logging
from datetime import datetime

from django.db.models import Sum
from django.views.decorators.cache import cache_page
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Transaction, RebateClaim
from .serializers import (
    RebateProgramSerializer,
    TransactionSerializer,
)

logger = logging.getLogger()


@api_view(['GET'])
def health(request):
    """Health check with DB status"""
    try:
        Transaction.objects.exists()
        return Response({"status": "Healthy"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "Unhealthy", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def create_rebate_program(request):
    """Create a new rebate program"""
    serializer = RebateProgramSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()

        logger.info("Successfully created a new rebate program: {}".format(serializer.data["rebate_program_id"]))

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def create_transaction(request):
    """Create a new transaction"""
    serializer = TransactionSerializer(data=request.data)

    if serializer.is_valid():
        transaction = serializer.save()
        transaction.check_eligibility()

        logger.info("Successfully created a new transaction: {}".format(serializer.data["transaction_id"]))

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@cache_page(60 * 15)
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

    if transaction.rebate_program:
        rebate_amount = transaction.get_rebate_amount()
        return Response(
            {'rebate_amount': rebate_amount},
            status=status.HTTP_200_OK,
        )
    return Response(
        {'No rebate program is associated with transaction.'}, status=status.HTTP_404_NOT_FOUND
    )


@api_view(['POST'])
def claim_rebate(request):
    """Claim rebate for eligible transactions"""
    transactions = (Transaction.objects
                    .filter(eligibility_status="eligible")
                    .exclude(rebate_claims__claim_status__in=["pending", "approved"]))

    created_claims = 0
    created_claims_id = []
    for transaction in transactions:
        rebate_claim = RebateClaim(
            transaction=transaction,
            claim_amount=transaction.get_rebate_amount(),
            claim_date=datetime.now().date(),
        )
        rebate_claim.save()
        created_claims += 1
        created_claims_id.append(rebate_claim.claim_id)
        logger.info("Successfully created a pending claim for transaction: {}".format(transaction.transaction_id))

    return Response(
        {"message": f"{created_claims} rebate claims successfully created."
              f"{created_claims_id}"},
        status=status.HTTP_200_OK,
    )


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

    if period_start > period_end:
        return Response({'error': 'Invalid period. Start date should be before end date.'},
                        status=status.HTTP_400_BAD_REQUEST)

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

@api_view(['PUT'])
def reject_claim(request, claim_id):
    """Reject a claim"""
    try :
      claim = RebateClaim.objects.get(pk=claim_id)
    except RebateClaim.DoesNotExist:
        return Response(
            {'error': 'Claim not found.'}, status=status.HTTP_404_NOT_FOUND
        )

    if claim.claim_status == "approved":
        return Response(
            {'error': 'Claim already approved.'}, status=status.HTTP_400_BAD_REQUEST
        )

    claim.reject()

    return Response(status=status.HTTP_200_OK)

@api_view(['PUT'])
def approve_claim(request, claim_id):
    """Reject a claim"""
    try :
      claim = RebateClaim.objects.get(pk=claim_id)
    except RebateClaim.DoesNotExist:
        return Response(
            {'error': 'Claim not found.'}, status=status.HTTP_404_NOT_FOUND
        )

    if claim.claim_status == "approved":
        return Response(
            {'error': 'Claim already rejected.'}, status=status.HTTP_400_BAD_REQUEST
        )

    claim.approve()

    return Response(status=status.HTTP_200_OK)