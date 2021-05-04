import React from "react";
import { useCookies } from 'react-cookie';
import { Redirect } from 'react-router-dom';
import { pullPatientData, pullPatientDataForNumber } from '../api';
import Select from 'react-select'

const Home = () => {
    const [cookies, _, removeCookie] = useCookies(['token']);
    const [patientData, setPatientData] = React.useState({});
    const [impersonateOptions, setImpersonateOptions] = React.useState([]);
    const [impersonating, setImpersonating] = React.useState(null);

    React.useEffect(() => {
        const loadData = async () => {
            const loadedData = await pullPatientData();
            if (loadedData === null) {
                removeCookie("token");
            }
            setPatientData(loadedData);
            if (loadedData.impersonateList) {
                setImpersonateOptions(
                    loadedData.impersonateList.map((tuple_data) => { return { label: tuple_data[0], value: tuple_data[1]}})
                );
            }
        }
        if (cookies.token) {
            loadData();
        }
    }, [cookies.token, removeCookie]);


    const loadDataForUser = async (selectedUser) => {
        const loadedData = await pullPatientDataForNumber(selectedUser.value);
        setPatientData(loadedData);
        setImpersonating(selectedUser.label);
    }

    const logout = () => {
        removeCookie("token");
    }

    return (
        <>
            {cookies.token ? (<p>Logged in!</p>) : <Redirect to="/login"/>}
            <p>{JSON.stringify(patientData)}</p>
            <button onClick={logout}>Logout</button>
            {patientData.impersonateList ? <Select options={impersonateOptions} onChange={(selectedValue) => { loadDataForUser(selectedValue)}}/> : null}
            {impersonating ? <p>Impersonating {impersonating}</p> : null}
        </>
    )
}

export default Home;