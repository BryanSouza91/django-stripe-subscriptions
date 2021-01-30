import os
import json
import stripe
from http import HTTPStatus

from django.http import JsonResponse
from django.views.generic import TemplateView, View


class Index(TemplateView):
    """
    route('/', methods=['GET'])
    """

    template_name = "index.html"


class Prices(TemplateView):
    """
    route('/prices', methods=['POST'])
    """

    template_name = "prices.html"


class Account(TemplateView):
    """
    route('account/', methods=['GET'])
    """

    template_name = "account.html"


class Config(View):
    """
    route('/config', methods=['GET'])
    """

    def get(self, request, *args, **kwargs):
        return JsonResponse(
            {
                "publishableKey": os.getenv("STRIPE_PUBLISHABLE_KEY"),
            }
        )


class CreateCustomer(View):
    """
    route('/create-customer', methods=['POST'])
    """

    def post(self, request, *args, **kwargs):
        # Reads application/json and returns a response
        data = json.loads(request.body)
        try:
            # Create a new customer object
            customer = stripe.Customer.create(email=data["email"], name=data["name"])
            # At this point, associate the ID of the Customer object with your
            # own internal representation of a customer, if you have one.

            return JsonResponse({"customer": customer})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=HTTPStatus.FORBIDDEN)


class CreateSubscription(View):
    """
    route('/create-subscription', methods=['POST'])
    """

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        try:

            stripe.PaymentMethod.attach(
                data["paymentMethodId"],
                customer=data["customerId"],
            )
            # Set the default payment method on the customer
            stripe.Customer.modify(
                data["customerId"],
                invoice_settings={
                    "default_payment_method": data["paymentMethodId"],
                },
            )
            print(data["priceId"])
            print(os.getenv(data["priceId"]))
            # Create the subscription
            subscription = stripe.Subscription.create(
                customer=data["customerId"],
                items=[{"price": os.getenv(data["priceId"])}],
                expand=["latest_invoice.payment_intent"],
            )
            return JsonResponse(subscription)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=HTTPStatus.OK)


class RetrySubscription(View):
    """
    route('/retry-invoice', methods=['POST'])
    """

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        try:

            payment_method = stripe.PaymentMethod.attach(
                data["paymentMethodId"],
                customer=data["customerId"],
            )
            # Set the default payment method on the customer
            stripe.Customer.modify(
                data["customerId"],
                invoice_settings={
                    "default_payment_method": payment_method.id,
                },
            )

            invoice = stripe.Invoice.retrieve(
                data["invoiceId"],
                expand=["payment_intent"],
            )
            return JsonResponse(invoice)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=HTTPStatus.OK)


class RetrieveCustomerPaymentMethod(View):
    """
    route('/retrieve-customer-payment-method', methods=['POST'])
    """

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        try:
            paymentMethod = stripe.PaymentMethod.retrieve(
                data["paymentMethodId"],
            )
            return JsonResponse(paymentMethod)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=HTTPStatus.FORBIDDEN)


class RetrieveUpcomingInvoice(View):
    """
    route('/retrieve-upcoming-invoice', methods=['POST'])
    """

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        try:
            # Retrieve the subscription
            subscription = stripe.Subscription.retrieve(data["subscriptionId"])

            # Retrieve the Invoice
            invoice = stripe.Invoice.upcoming(
                customer=data["customerId"],
                subscription=data["subscriptionId"],
                subscription_items=[
                    {"id": subscription["items"]["data"][0].id, "deleted": True},
                    {"price": os.getenv(data["newPriceId"]), "deleted": False},
                ],
            )
            return JsonResponse(invoice)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=HTTPStatus.FORBIDDEN)


class UpdateSubscription(View):
    """
    route('/update-subscription', methods=['POST'])
    """

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        try:
            subscription = stripe.Subscription.retrieve(data["subscriptionId"])

            updatedSubscription = stripe.Subscription.modify(
                data["subscriptionId"],
                cancel_at_period_end=False,
                items=[
                    {
                        "id": subscription["items"]["data"][0].id,
                        "price": os.getenv(data["newPriceId"]),
                    }
                ],
            )
            return JsonResponse(updatedSubscription)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=HTTPStatus.FORBIDDEN)


class CancelSubscription(View):
    """
    route('/cancel-subscription', methods=['POST'])
    """

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        try:
            # Cancel the subscription by deleting it
            deletedSubscription = stripe.Subscription.delete(data["subscriptionId"])
            return JsonResponse(deletedSubscription)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=HTTPStatus.FORBIDDEN)


class Webhook(View):
    """
    route('/stripe-webhook', methods=['POST'])
    """

    def post(self, request, *args, **kwargs):

        # You can use webhooks to receive information about asynchronous payment events.
        # For more about our webhook events check out https://stripe.com/docs/webhooks.
        webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        request_data = json.loads(request.body)

        if webhook_secret:
            # Retrieve the event by verifying the signature using the raw body and secret if webhook signing is configured.
            signature = request.headers.get("stripe-signature")
            try:
                event = stripe.Webhook.construct_event(
                    payload=request.body, sig_header=signature, secret=webhook_secret
                )
                data = event["data"]
            except Exception as e:
                return e
            # Get the type of webhook event sent - used to check the status of PaymentIntents.
            event_type = event["type"]
        else:
            data = request_data["data"]
            event_type = request_data["type"]

        # data_object = data['object']

        if event_type == "invoice.paid":
            # Used to provision services after the trial has ended.
            # The status of the invoice will show up as paid. Store the status in your
            # database to reference when a user accesses your service to avoid hitting rate
            # limits.
            print(data)

        if event_type == "invoice.payment_failed":
            # If the payment fails or the customer does not have a valid payment method,
            # an invoice.payment_failed event is sent, the subscription becomes past_due.
            # Use this webhook to notify your user that their payment has
            # failed and to retrieve new card details.
            print(data)

        if event_type == "invoice.finalized":
            # If you want to manually send out invoices to your customers
            # or store them locally to reference to avoid hitting Stripe rate limits.
            print(data)

        if event_type == "customer.subscription.deleted":
            # handle subscription cancelled automatically based
            # upon your subscription settings. Or if the user cancels it.
            print(data)

        if event_type == "customer.subscription.trial_will_end":
            # Send notification to your user that the trial will end
            print(data)

        return JsonResponse({"status": "success"})
