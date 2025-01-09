from django.core.cache import cache
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
            'eligibility_status',
            'rebate_program',
        ]

    def to_internal_value(self, data):
        """Override to check cache for RebateProgram before fetching from DB"""
        global rebate_program
        rebate_program_id = data.pop('rebate_program')

        if rebate_program_id:
            cached_rebate_program = cache.get(f'rebate_program_{rebate_program_id}')

            if cached_rebate_program:
                rebate_program = cached_rebate_program
            else:
                try:
                    rebate_program = RebateProgram.objects.get(rebate_program_id=rebate_program_id)

                    cache.set(f'rebate_program_{rebate_program_id}', rebate_program,
                              timeout=60 * 60)
                except RebateProgram.DoesNotExist:
                    raise serializers.ValidationError({
                        'rebate_program': f'Rebate Program with ID "{rebate_program_id}" does not exist.'
                    })

        # Call super with remaining data
        validated_data = super().to_internal_value(data)
        # Add the rebate_program object to validated_data
        validated_data['rebate_program'] = rebate_program

        return validated_data
