import uuid

from django.db import models

from RebateService.specifications import MinAmountSpecification, TransactionDateRangeSpecification, AndSpecification


class RebateProgram(models.Model):
    rebate_program_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    program_name = models.CharField(max_length=255)
    rebate_percentage = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    eligibility_criteria = models.JSONField()

    def __str__(self):
        return self.program_name


class Transaction(models.Model):
    transaction_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    amount = models.IntegerField()
    transaction_date = models.DateField()
    rebate_program = models.ForeignKey(RebateProgram, on_delete=models.PROTECT, related_name="transactions")
    eligibility_status = models.CharField(
        max_length=20,
        choices=[
            ("eligible", "Eligible"),
            ("not_eligible", "Not Eligible")
        ],
        default="not_eligible"
    )

    def __str__(self):
        return str(self.transaction_id)

    def get_rebate_percentage(self):
        return self.rebate_program.rebate_percentage

    def get_rebate_amount(self):
        return (self.amount * self.get_rebate_percentage()) / 100

    def check_eligibility(self):
        specs = []

        if 'minimal_count' in self.rebate_program.eligibility_criteria:
            specs.append(MinAmountSpecification(self.rebate_program.eligibility_criteria['minimal_count']))

        specs.append(TransactionDateRangeSpecification(
            self.rebate_program.start_date,
            self.rebate_program.end_date
        ))

        combined_spec = AndSpecification(*specs)

        if combined_spec.is_satisfied_by(self):
            self.eligibility_status = "eligible"
        else:
            self.eligibility_status = "not_eligible"

        self.save()


class RebateClaim(models.Model):
    claim_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(Transaction, on_delete=models.PROTECT, related_name="rebate_claims")
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
    claim_date = models.DateField()

    def __str__(self):
        return str(self.claim_id)

    def save(self, *args, **kwargs):
        # Ensure only one approved claim per transaction
        if (
                self.claim_status == "approved"
                and RebateClaim.objects.filter(transaction=self.transaction, claim_status="approved").exclude(
            pk=self.pk).exists()
        ):
            raise ValueError("A transaction can only have one approved claim.")

        # Optional: Ensure only one pending claim per transaction (if required by your business logic)
        if (
                self.claim_status == "pending"
                and RebateClaim.objects.filter(transaction=self.transaction, claim_status="pending").exclude(
            pk=self.pk).exists()
        ):
            raise ValueError("A transaction can only have one pending claim.")

        super().save(*args, **kwargs)
