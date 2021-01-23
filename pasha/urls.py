from django.urls import path
from . import views

urlpatterns = [
    path("", views.Index.as_view(), name="home"),
    path("prices/", views.Prices.as_view(), name="prices"),
    path("account/", views.Account.as_view(), name="account"),
    path("config/", views.Config.as_view(), name="config"),
    path("create-customer/", views.CreateCustomer.as_view(), name="create-customer"),
    path(
        "create-subscription/",
        views.CreateSubscription.as_view(),
        name="create-subscription",
    ),
    path(
        "retrieve-customer-payment-method/",
        views.RetrieveCustomerPaymentMethod.as_view(),
        name="retrieve-customer-payment-method",
    ),
    path(
        "retrieve-upcoming-invoice/",
        views.RetrieveUpcomingInvoice.as_view(),
        name="retrieve-upcoming-invoice",
    ),
    path(
        "update-subscription/",
        views.UpdateSubscription.as_view(),
        name="update-subscription",
    ),
    path(
        "cancel-subscription/",
        views.CancelSubscription.as_view(),
        name="cancel-subscription",
    ),
    path("stripe-webhook/", views.Webhook.as_view(), name="stripe-webhook"),
]