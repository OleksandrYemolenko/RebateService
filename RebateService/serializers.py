from rest_framework import serializers

from .models import RebateProgram, Transaction


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

    def validate_rebate_percentage(self, value):
        if value <= 0 or value > 100:
            raise serializers.ValidationError(
                'A rebate should have valid percentage.'
            )
        return value

    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if start_date > end_date:
            raise serializers.ValidationError("Start date must be before end date.")
        return data


class TransactionSerializer(serializers.ModelSerializer):
    rebate_program = serializers.PrimaryKeyRelatedField(
        queryset=RebateProgram.objects.all(),
        error_messages={
            'does_not_exist': 'Rebate Program with the provided ID does not exist.'
        }
    )

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

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Transaction amount must be greater than zero.")
        return value
