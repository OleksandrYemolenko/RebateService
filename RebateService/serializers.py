from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import RebateProgram, Transaction, RebateClaim


class RebateProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = RebateProgram
        fields = [
            'rebate_program_id',
            'program_name',
            'rebate_percentage',
            'start_date',
            'end_date',
            'eligibility_criteria',
        ]


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'transaction_id',
            'amount',
            'transaction_date',
            'rebate_program',
            'eligibility_status',
        ]
        read_only_fields = [
            'eligibility_status'
        ]


class RebateClaimSerializer(serializers.ModelSerializer):
    transaction = serializers.PrimaryKeyRelatedField(queryset=Transaction.objects.all())

    class Meta:
        model = RebateClaim
        fields = [
            'claim_id',
            'transaction',
            'claim_amount',
            'claim_status',
            'claim_date',
        ]

    def validate(self, data):
        """
        Ensure that a rebate can only be claimed once for each transaction.
        """
        transaction = data.get('transaction')
        if RebateClaim.objects.filter(transaction=transaction).exists():
            raise serializers.ValidationError(
                'A rebate has already been claimed for this transaction.'
            )
        return data
