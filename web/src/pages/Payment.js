import React from "react";
import { Box, Button, Heading, Paragraph, Spinner } from "grommet";
import { pullPatientPaymentData } from "../api";
import { useCookies } from 'react-cookie';
import { useHistory } from "react-router-dom";

import { DateTime } from "luxon";
import { Elements } from '@stripe/react-stripe-js';

import {loadStripe} from '@stripe/stripe-js';

import StripeCardEntry from "../components/StripeCardEntry";

const Payment = () => {
      // Initialize an instance of stripe.

    const [loading, setLoading] = React.useState(true);
    const [paymentData, setPaymentData] = React.useState(null);
    const [_, __, removeCookie] = useCookies(['token']);
    const history = useHistory();
    const loadData = React.useCallback(async () => {
        setLoading(true);
        let loadedData = await pullPatientPaymentData();
        if (loadedData === null) {
            removeCookie("token");
            history.push("/login");
        }
        console.log(loadedData.state);
        if (["intro", "dose_windows_requested", "dose_window_times_requested", "timezone_requested"].includes(loadedData.state)) {
            history.push("/finishOnboarding");
        }
        setPaymentData(loadedData);
        setLoading(false);
    }, [history, removeCookie]);

    React.useEffect(() => {
        if (loading) {
            loadData();
        }
    }, [loadData, loading])

    if (loading) {
        return <Spinner />
    }

    if (paymentData.state === 'payment_method_requested') {
        const stripePromise = loadStripe(paymentData.publishable_key);
        return (
            <Elements stripe={stripePromise}>
                <Box padding="large">
                    <Heading size="small">Enter payment information</Heading>
                    <Paragraph>Looking forward to helping you with your medication. If you have any questions before signing up, please reach out to us over text at (650) 667-1146.</Paragraph>
                    <StripeCardEntry
                        submitText="Start Coherence subscription ($6.99)"
                        clientSecret={paymentData.client_secret}
                        afterSubmitAction={loadData}
                    />
                </Box>
            </Elements>
        );
    } else if (paymentData.state === "payment_verification_pending") {
        return <Paragraph>We're verifying your payment information. You'll get a text when you're verified with further instructions. Thanks for your patience!</Paragraph>
    } else if (paymentData.state === "subscription_expired") {
        return (
            <Box>
                <Paragraph>Your subscription ended on {DateTime.fromHTTP(paymentData.subscription_end_date).toLocaleString(DateTime.DATE_MED)}.</Paragraph>
                <Button label="Renew for $6.99"/>
            </Box>
        );
    } else if (["paused", "active"].includes(paymentData.state)) {
        return (
            <Box margin="large">
                <Heading size="small">Manage your subscription</Heading>
                {paymentData.payment_method ? (
                    <>
                        <Paragraph alignSelf="center">Your subscription will be automatically renewed on {DateTime.fromHTTP(paymentData.subscription_end_date).toLocaleString(DateTime.DATE_MED)}.</Paragraph>
                        <Paragraph alignSelf="center">Payment data on file: {paymentData.payment_method.brand} ending in {paymentData.payment_method.last4}</Paragraph>
                    </>
                ): (
                    <>
                        <Paragraph alignSelf="center">Your free trial will end on {DateTime.fromHTTP(paymentData.subscription_end_date).toLocaleString(DateTime.DATE_MED)}.</Paragraph>
                        <Button label="Enter payment information"/>
                    </>
                )
                }

                <Box direction="row" justify="between">
                    <Button label="Go back" margin={{vertical: "small"}} onClick={() => {history.push("/")}}/>
                    <Button label={paymentData.payment_method ? "Cancel subscription" : "Stop free trial"} margin={{vertical: "small"}}/>
                </Box>
            </Box>
        );
    }
}

export default Payment;