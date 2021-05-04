import React from "react";
import { useCookies } from 'react-cookie';
import { Redirect } from 'react-router-dom';
import { pullPatientData } from '../api';

const Home = () => {
    const [cookies, _, removeCookie] = useCookies(['token']);
    const [patientData, setPatientData] = React.useState({});

    React.useEffect(() => {
        const loadData = async () => {
            const loadedData = await pullPatientData();
            setPatientData(loadedData);
        }
        if (cookies.token) {
            loadData();
        }
    }, [cookies.token]);

    const logout = () => {
        removeCookie("token");
    }

    return (
        <>
            {cookies.token ? (<p>Logged in!</p>) : <Redirect to="/login"/>}
            <p>{JSON.stringify(patientData)}</p>
            <button onClick={logout}>Logout</button>
        </>
    )
}

export default Home;