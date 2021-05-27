import React from "react";

import { Paragraph } from "grommet";
import { useHistory } from "react-router-dom";

import { getPatientState } from "../api";

const FinishOnboarding = () => {
    const history = useHistory();
    React.useEffect(() => {
        const loadState = async () => {
            const { state } = await getPatientState();
            if (["active", "paused"].includes(state)) {
                history.push("/");
            }
        }
        loadState();
    }, [history]);
    return <Paragraph>Hello there! Be sure to enter your information over text before continuing here. Thanks!</Paragraph>
}

export default FinishOnboarding;