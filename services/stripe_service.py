
import os
from decimal import Decimal, ROUND_HALF_UP

import stripe
from dotenv import load_dotenv

load_dotenv()

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173",
).rstrip("/")


def _configure_stripe():
    """
    Load and configure the Stripe secret key.
    """
    secret_key = os.getenv("STRIPE_SECRET_KEY")

    if not secret_key:
        raise RuntimeError(
            "STRIPE_SECRET_KEY is not configured in the .env file"
        )

    stripe.api_key = secret_key


def _to_stripe_amount(amount) -> int:
    """
    Convert a database price into Stripe's smallest
    currency unit.

    Example:
        49.99 USD -> 4999 cents
    """
    decimal_amount = Decimal(str(amount))

    cents = (
        decimal_amount * Decimal("100")
    ).quantize(
        Decimal("1"),
        rounding=ROUND_HALF_UP,
    )

    return int(cents)


def create_checkout_session(
    *,
    order_id: int,
    user_email: str,
    items,
):
    """
    Create a Stripe Checkout Session.

    Prices are taken from the database.
    The frontend does not provide prices.
    """

    _configure_stripe()

    if not items:
        raise ValueError(
            "Cannot create checkout session for an empty order"
        )

    line_items = []

    for item in items:
        unit_amount = _to_stripe_amount(
            item.unit_price
        )

        if unit_amount <= 0:
            raise ValueError(
                f"Invalid price for product: "
                f"{item.product_name}"
            )

        if item.quantity <= 0:
            raise ValueError(
                f"Invalid quantity for product: "
                f"{item.product_name}"
            )

        line_items.append(
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": item.product_name,
                    },
                    "unit_amount": unit_amount,
                },
                "quantity": item.quantity,
            }
        )

    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=line_items,
        success_url=(
            f"{FRONTEND_URL}"
            "/payment-success"
            "?session_id={CHECKOUT_SESSION_ID}"
        ),
        cancel_url=f"{FRONTEND_URL}/cart",
        customer_email=user_email,
        metadata={
            "order_id": str(order_id),
        },
        payment_intent_data={
            "metadata": {
                "order_id": str(order_id),
            }
        },
    )

    return session


def construct_webhook_event(
    payload: bytes,
    signature: str,
    secret: str,
):
    """
    Verify the Stripe webhook signature and
    construct the Stripe event.

    The webhook payload must be verified before
    processing any payment information.
    """

    if not signature:
        raise ValueError(
            "Missing Stripe-Signature header"
        )

    if not secret:
        raise ValueError(
            "Stripe webhook secret is not configured"
        )

    return stripe.Webhook.construct_event(
        payload,
        signature,
        secret,
    )
