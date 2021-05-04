import React from "react";
import { useCookies } from 'react-cookie';
import { Redirect } from 'react-router-dom';
import { pullPatientData } from '../api';
import Select from 'react-select'

const Home = () => {
    const [cookies, _, removeCookie] = useCookies(['token']);
    const [patientData, setPatientData] = React.useState({});


    const options = [
        { value: 'chocolate', label: 'Chocolate' },
        { value: 'strawberry', label: 'Strawberry' },
        { value: 'vanilla', label: 'Vanilla' }
    ]

    React.useEffect(() => {
        const loadData = async () => {
            const loadedData = await pullPatientData();
            if (loadedData === null) {
                removeCookie("token");
            }
            setPatientData(loadedData);
        }
        if (cookies.token) {
            loadData();
        }
    }, [cookies.token, removeCookie]);

    const logout = () => {
        removeCookie("token");
    }

    return (
        <>
            {cookies.token ? (<p>Logged in!</p>) : <Redirect to="/login"/>}
            <p>{JSON.stringify(patientData)}</p>
            <button onClick={logout}>Logout</button>
            <Select options={options}/>
        </>
    )
}

export default Home;