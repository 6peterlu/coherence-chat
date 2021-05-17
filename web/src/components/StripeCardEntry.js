import React from "react";
import {
    CardElement,
    useStripe,
    useElements,
  } from '@stripe/react-stripe-js';
import AnimatingButton from "../components/AnimatingButton";
import { Paragraph, Spinner } from "grommet";

const StripeCardEntry = ({submitText, clientSecret, afterSubmitAction}) => {
    const stripe = useStripe();
    const elements = useElements();
    const [validatingCard, setValidatingCard] = React.useState(false);
    if (!stripe || !elements) {
        // Stripe.js has not loaded yet. Make sure to disable
        // form submission until Stripe.js has loaded.
        return <Spinner />;
    }

    // Use card Element to tokenize payment details
    const submitPayment = async () => {
        const cardElement = elements.getElement(CardElement);
        setValidatingCard(true);
        let { error, paymentIntent } = await stripe.confirmCardPayment(clientSecret, {
            payment_method: {
                card: cardElement,
                billing_details: {
                    name: "Peter Lu"
                },
            },
            setup_future_usage: "off_session"  // allows us to charge card while not in checkout flow
        });
        setValidatingCard(false);
        console.log(error);
        console.log(paymentIntent);
    }
    return (
        <>
            <CardElement />
            <AnimatingButton
                label={submitText ? submitText : "Save payment information"}
                onClick={async () => {
                    await submitPayment();
                    afterSubmitAction();  // any reloading that needs to be done after submitting payment info
                }}
                animating={validatingCard}
            />
            {validatingCard ? <Paragraph>Submitting your payment information. Please do not close this window.</Paragraph> : null}
        </>
    )
}

export default StripeCardEntry;