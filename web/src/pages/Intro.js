import React from "react";
import { login } from "../api";

const Intro = () => {
    const [phoneNumber, setPhoneNumber] = React.useState("");
    const [secretCode, setSecretCode] = React.useState("");
    const [password, setPassword] = React.useState("");
    const [componentToDisplay, setComponentToDisplay] = React.useState("phoneNumber");
    const submitAll = React.useCallback(async () => {
        const response = await login(phoneNumber, secretCode, password);
        setComponentToDisplay(response.status);
    }, [password, phoneNumber, secretCode])
    const getInputField = React.useCallback(() => {
        if (componentToDisplay === "phoneNumber") {
            return <>
                <p>Enter phone number</p>
                <input type="text" onChange={(event) => {setPhoneNumber(event.target.value)}} value={phoneNumber}/>
                <button onClick={submitAll}>Submit</button>
            </>
        } else if (componentToDisplay === "2fa") {
            return <>
                <p>Enter secret code</p>
                <input type="text" onChange={(event) => {setSecretCode(event.target.value)}} value={secretCode}/>
                <button onClick={submitAll}>Submit</button>
            </>
        } else if (componentToDisplay === "password") {
            return <>
                <p>Enter password</p>
                <input type="text" onChange={(event) => {setPassword(event.target.value)}} value={password}/>
                <button onClick={submitAll}>Submit</button>
            </>
        } else if (componentToDisplay === "register") {
            return <>
                <p>Create your password</p>
                <input type="text" onChange={(event) => {setPassword(event.target.value)}} value={password}/>
                <button onClick={submitAll}>Submit</button>
            </>
        }
    }, [componentToDisplay, password, phoneNumber, secretCode, submitAll])
    return (
        <>
            <p>intro</p>
            { getInputField() }
        </>
    )
}

export default Intro;