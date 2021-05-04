import React from "react";
import { login } from "../api";
import { useCookies } from 'react-cookie';
import { Redirect } from 'react-router-dom';

const Intro = () => {
    const [phoneNumber, setPhoneNumber] = React.useState("");
    const [secretCode, setSecretCode] = React.useState("");
    const [password, setPassword] = React.useState("");
    const [componentToDisplay, setComponentToDisplay] = React.useState("phoneNumber");
    const [cookies, setCookie] = useCookies(["token"]);
    const [authError, setAuthError] = React.useState(false);
    const submitAll = React.useCallback(async () => {
        const response = await login(phoneNumber, secretCode, password);
        console.log(response);
        if (response === null) {
            setAuthError(true);
        } else {
            if (response.status === "success") {
                console.log("setting cookie");
                setCookie("token", response.token);
            }
            setComponentToDisplay(response.status);
            setAuthError(false);
        }
    }, [password, phoneNumber, secretCode, setCookie])
    const getInputField = React.useCallback(() => {
        if (componentToDisplay === "phoneNumber") {
            return <>
                <p>Enter phone number</p>
                <input type="text" onChange={(event) => {setPhoneNumber(event.target.value)}} value={phoneNumber}/>
                <button onClick={submitAll}>Submit</button>
                {authError ? <p>Invalid phone number.</p> : null}
            </>
        } else if (componentToDisplay === "2fa") {
            return <>
                <p>Enter secret code</p>
                <input type="text" onChange={(event) => {setSecretCode(event.target.value)}} value={secretCode}/>
                <button onClick={submitAll}>Submit</button>
                {authError ? <p>Invalid secret code.</p> : null}
            </>
        } else if (componentToDisplay === "password") {
            return <>
                <p>Enter password</p>
                <input type="text" onChange={(event) => {setPassword(event.target.value)}} value={password}/>
                <button onClick={submitAll}>Submit</button>
                {authError ? <p>Invalid password.</p> : null}
            </>
        } else if (componentToDisplay === "register") {
            return <>
                <p>Create your password</p>
                <input type="text" onChange={(event) => {setPassword(event.target.value)}} value={password}/>
                <button onClick={submitAll}>Submit</button>
            </>
        }
    }, [authError, componentToDisplay, password, phoneNumber, secretCode, submitAll])
    if (cookies.token) {
        return <Redirect to="/"/>;
    }
    return (
        <>
            <p>intro</p>
            { getInputField() }
        </>
    )
}

export default Intro;