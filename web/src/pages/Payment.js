import React from "react";
import { Box, Button, Heading, Layer, Paragraph, Spinner } from "grommet";
import { cancelSubscription, pullPatientPaymentData, renewSubscription, submitPaymentInfo } from "../api";
import { useCookies } from 'react-cookie';
import { useHistory } from "react-router-dom";

import { DateTime } from "luxon";
import { Elements } from '@stripe/react-stripe-js';

import {loadStripe} from '@stripe/stripe-js';

import StripeCardEntry from "../components/StripeCardEntry";
import { Close } from "grommet-icons";
import AnimatingButton from "../components/AnimatingButton";

const Payment = () => {
      // Initialize an instance of stripe.
    const [loading, setLoading] = React.useState(true);
    const [animating, setAnimating] = React.useState(false);
    const [paymentData, setPaymentData] = React.useState(null);
    const [addCardModalVisible, setAddCardModalVisible] = React.useState(false);
    const [payWithCardModalVisible, setPayWithCardModalVisible] = React.useState(false);
    const [_, __, removeCookie] = useCookies(['token']);
    const history = useHistory();
    const loadData = React.useCallback(async () => {
        setLoading(true);
        let loadedData = await pullPatientPaymentData();
        if (loadedData === null) {
            removeCookie("token");
            history.push("/welcome");
        }
        console.log(loadedData.state);
        if (["intro", "dose_windows_requested", "dose_window_times_requested", "timezone_requested"].includes(loadedData.state)) {
            history.push("/finishOnboarding");
        }
        setPaymentData(loadedData);
        setLoading(false);
        setAnimating(false);
    }, [history, removeCookie]);

    const stripePromise = React.useMemo(() => {
        return paymentData !== null ? loadStripe(paymentData.publishable_key) : null;
    }, [paymentData]);

    React.useEffect(() => {
        if (loading) {
            loadData();
        }
    }, [loadData, loading]);

    if (loading) {
        return <Spinner />
    }
    if (paymentData.secondary_state === "payment_verification_pending") {
        return <Paragraph>We're verifying your payment information. You'll get a text when you're verified with further instructions. Thanks for your patience!</Paragraph>
    } else if (paymentData.state === 'payment_method_requested') {
        return (
            <Elements stripe={stripePromise}>
                <Box margin="large">
                    <Heading size="small">Enter payment information</Heading>
                    <Paragraph>Looking forward to helping you with your medication. If you have any questions before signing up, please reach out to us over text at (650) 667-1146.</Paragraph>
                    <StripeCardEntry
                        submitText="Start Coherence subscription ($6.99)"
                        clientSecret={paymentData.client_secret}
                        afterSubmitAction={loadData}
                        payOnSubmit={true}
                    />
                </Box>
            </Elements>
        );
    } else if (["paused", "active", "subscription_expired"].includes(paymentData.state)) {
        return (
                <Box margin="large">
                    <Heading size="small">Manage your subscription</Heading>
                    {paymentData.state === "subscription_expired" ? (
                        <>
                            <Paragraph alignSelf="center">Your subscription expired on {DateTime.fromHTTP(paymentData.subscription_end_date).toLocaleString(DateTime.DATE_MED)}.</Paragraph>
                            {paymentData.payment_method ? (
                                <AnimatingButton
                                    label="Renew for $6.99"
                                    onClick={async () => {
                                        setAnimating(true);
                                        console.log("attempting to renew subscription");
                                        await submitPaymentInfo();
                                        await renewSubscription();
                                        setLoading(true);
                                    }}
                                    animating={animating}
                                    primary={true}
                                />
                            ) : (
                                <>
                                    <Button
                                        label="Renew for $6.99"
                                        onClick={() => {setPayWithCardModalVisible(true)}}
                                        primary={true}
                                    />
                                    {payWithCardModalVisible ? (
                                        <Layer
                                            responsive={false}
                                            onEsc={() => setPayWithCardModalVisible(false)}
                                            onClickOutside={() => setPayWithCardModalVisible(false)}
                                            animation={false}
                                        >
                                            <Box width="90vw" pad="large">
                                                <Box direction="row" justify="between">
                                                    <Paragraph size="large">Enter credit card information</Paragraph>
                                                    <Button icon={<Close />} onClick={() => setPayWithCardModalVisible(false)}/>
                                                </Box>
                                                    <Elements stripe={stripePromise}>
                                                        <StripeCardEntry
                                                            submitText="Start Coherence subscription ($6.99)"
                                                            clientSecret={paymentData.client_secret}
                                                            afterSubmitAction={loadData}
                                                            payOnSubmit={true}
                                                        />
                                                    </Elements>
                                                    {/* <Paragraph>stripe element</Paragraph> */}
                                            </Box>
                                        </Layer>
                                    ) : null}
                                </>
                            )}
                        </>
                    ) : paymentData.payment_method ? (
                        <>
                            <Paragraph alignSelf="center">Your subscription will be automatically renewed on {DateTime.fromHTTP(paymentData.subscription_end_date).toLocaleString(DateTime.DATE_MED)}.</Paragraph>
                            <Paragraph alignSelf="center">Payment data on file: {paymentData.payment_method.brand} ending in {paymentData.payment_method.last4}</Paragraph>
                        </>
                    ): (
                        <>
                            <Paragraph alignSelf="center">Your free trial will end on {DateTime.fromHTTP(paymentData.subscription_end_date).toLocaleString(DateTime.DATE_MED)}.</Paragraph>
                            <Button label="Enter payment information" onClick={() => {setAddCardModalVisible(true)}}/>
                            {addCardModalVisible ? (
                                <Layer
                                    responsive={false}
                                    onEsc={() => setAddCardModalVisible(false)}
                                    onClickOutside={() => setAddCardModalVisible(false)}
                                    animation={false}
                                >
                                    <Box width="90vw" pad="large">
                                        <Box direction="row" justify="between">
                                            <Paragraph size="large">Enter credit card information</Paragraph>
                                            <Button icon={<Close />} onClick={() => setAddCardModalVisible(false)}/>
                                        </Box>
                                            <Elements stripe={stripePromise}>
                                                <StripeCardEntry
                                                    submitText={`Add card (will be charged on ${DateTime.fromHTTP(paymentData.subscription_end_date).toLocaleString(DateTime.DATE_MED)}.)`}
                                                    clientSecret={paymentData.client_secret}
                                                    afterSubmitAction={async () => {
                                                        await loadData();
                                                        setAddCardModalVisible(false);
                                                    }}
                                                    payOnSubmit={false}
                                                />
                                            </Elements>
                                            {/* <Paragraph>stripe element</Paragraph> */}
                                    </Box>
                                </Layer>
                            ) : null}
                        </>
                    )
                    }
                    <Box direction="row" justify="between">
                        <Button label="Go back" margin={{vertical: "small"}} onClick={() => {history.push("/")}}/>
                        {
                            <AnimatingButton
                                label={paymentData.payment_method ? "Cancel subscription" : "Stop free trial"}
                                margin={{vertical: "small"}}
                                onClick={async () => {
                                    setAnimating(true);
                                    await cancelSubscription();
                                    setLoading(true);
                                }}
                                animating={animating}
                                disabled={paymentData.state === "subscription_expired"}
                            />
                        }
                    </Box>
                </Box>

        );
    };
}

export default Payment;