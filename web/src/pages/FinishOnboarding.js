import React from "react";

import { Paragraph } from "grommet";
import { useHistory } from "react-router-dom";

import { getPatientState } from "../api";

const FinishOnboarding = () => {
    const history = useHistory();
    React.useEffect(() => {
        const loadState = async () => {
            const stateData = await getPatientState();
            if (stateData === null) {
                history.push("/welcome");
            } else if (["active", "paused"].includes(stateData.state)) {
                history.push("/");
            } else if (["payment_method_requested", "subscription_expired"].includes(stateData.state)) {
                history.push("/payment");
            }
        }
        loadState();
    }, [history]);
    return <Paragraph>Hello there! Be sure to enter your information over text before continuing here. Thanks!</Paragraph>
}

export default FinishOnboarding;