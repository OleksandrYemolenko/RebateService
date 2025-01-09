import uuid

from django.db import models


class RebateProgram(models.Model):
    rebate_program_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    program_name = models.CharField(max_length=255)
    rebate_percentage = models.IntegerField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    eligibility_criteria = models.JSONField()

    def __str__(self):
        return self.program_name


class Transaction(models.Model):
    transaction_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    amount = models.IntegerField()
    transaction_date = models.DateTimeField()
    rebate_program = models.ForeignKey(RebateProgram, on_delete=models.PROTECT, related_name="transactions")
    eligibility_status = models.CharField(
        max_length=20,
        choices=[
            ("eligible", "Eligible"),
            ("not_eligible", "Not Eligible")
        ]
    )

    def __str__(self):
        return str(self.transaction_id)

    def get_rebate_percentage(self):
        return self.rebate_program.rebate_percentage


class RebateClaim(models.Model):
    claim_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(Transaction, on_delete=models.PROTECT, related_name="rebate_claims", unique=True)
    claim_amount = models.IntegerField()
    claim_status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected")
        ],
        default="pending"
    )
    claim_date = models.DateTimeField()

    def __str__(self):
        return str(self.claim_id)
