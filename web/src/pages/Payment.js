import React from "react";
import { Paragraph } from "grommet";
import { pullPatientData } from "../api";
import { useCookies } from 'react-cookie';
import { useHistory } from "react-router-dom";

const Payment = () => {
    const [patientData, setPatientData] = React.useState(null);
    const [_, setCookie, removeCookie] = useCookies(['token']);
    const history = useHistory();
    const loadData = React.useCallback(async () => {
        let loadedData = await pullPatientData(5);  // TODO: split /patientData into multiple routes
        if (loadedData === null) {
            removeCookie("token");
            history.push("/login");
        }
        console.log(loadedData.state);
        if (["paused", "active"].includes(loadedData.state)) {
            history.push("/");
        }
        if (["intro", "dose_windows_requested", "dose_window_times_requested", "timezone_requested"].includes(loadedData.state)) {
            history.push("/finishOnboarding");
        }
        console.log(loadedData);
        setPatientData(loadedData);
        setCookie('token', loadedData.token, {secure: true});  // refresh login token
    }, [history, removeCookie, setCookie])
    React.useEffect(() => {
        if (patientData === null) {
            loadData();
        }
    }, [loadData, patientData])
    return <Paragraph>Enter payment info</Paragraph>;
}

export default Payment;