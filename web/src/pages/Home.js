import React from "react";
import { useCookies } from 'react-cookie';
import { Redirect } from 'react-router-dom';

const Home = () => {
    const [cookie] = useCookies(['token']);
    console.log(cookie)
    return (
        <>
            {cookie.token ? (<p>Logged in!</p>) : <Redirect to="/login"/>}
        </>
    )
}

export default Home;