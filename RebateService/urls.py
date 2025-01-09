"""
URL configuration for RebateService project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from . import views

urlpatterns = [
    path('health', views.health),
    path('api/v1/rebate-programs', views.create_rebate_program),
    path('api/v1/transactions', views.create_transaction),
    path('api/v1/transactions/<uuid:transaction_id>/rebate', views.calculate_rebate),
    path('api/v1/report', views.get_report),
    path('api/v1/claim', views.claim_open_transactions),
    path('api/v1/claim/<uuid:claim_id>/approve', views.approve_claim),
    path('api/v1/claim/<uuid:claim_id>/reject', views.reject_claim),
]
