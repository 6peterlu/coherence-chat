import React from "react";
import { login } from "../api";
import { useCookies } from 'react-cookie';
import { Redirect, useHistory } from 'react-router-dom';
import { Box, Paragraph, Heading, Button, TextInput } from "grommet";
import { Phone, Login, Fireball, Lock } from "grommet-icons";

const Intro = () => {
    const history = useHistory();
    const [phoneNumber, setPhoneNumber] = React.useState("");
    const [secretCode, setSecretCode] = React.useState("");
    const [password, setPassword] = React.useState("");
    const [passwordConfirm, setPasswordConfirm] = React.useState("");
    const [componentToDisplay, setComponentToDisplay] = React.useState("phoneNumber");
    const [cookies, setCookie] = useCookies(["token"]);
    const [authError, setAuthError] = React.useState(false);
    const submitAll = React.useCallback(async () => {
        const response = await login(phoneNumber, secretCode, password);
        if (response === null) {
            setAuthError(true);
        } else {
            if (response.status === "success") {
                console.log(`setting cookie to ${response.token}`);
                setCookie("token", response.token);
                if (response.state === "payment_method_requested") {
                    history.push("/payment");
                }
            }
            console.log(response);
            console.log(response.status);
            setComponentToDisplay(response.status);
            setAuthError(false);
        }
    }, [history, password, phoneNumber, secretCode, setCookie])
    const getInputField = React.useCallback(() => {
        if (componentToDisplay === "phoneNumber") {
            return <>
                <Paragraph textAlign="center" size="small">Enter phone number.</Paragraph>
                <TextInput
                    icon={<Phone/>}
                    placeholder="(555) 555-5555"
                    size="small"
                    value={phoneNumber}
                    onChange={(event) => {setPhoneNumber(event.target.value)}}
                />
                {authError ? <Paragraph size="small">Invalid phone number.</Paragraph> : null}
            </>
        } else if (componentToDisplay === "2fa") {
            return <>
                <Paragraph textAlign="center" size="small">We've texted you a secret code, enter it below.</Paragraph>
                <TextInput
                    icon={<Fireball />}
                    placeholder="123456"
                    size="small"
                    value={secretCode}
                    onChange={(event) => {setSecretCode(event.target.value)}}
                />
                {authError ? <Paragraph size="small">Invalid secret code.</Paragraph> : null}
            </>
        } else if (componentToDisplay === "password") {
            return <>
                <Paragraph textAlign="center" size="small">Enter password.</Paragraph>
                <TextInput
                    icon={<Lock />}
                    placeholder="•••••••••"
                    size="small"
                    value={password}
                    onChange={(event) => {
                        setPassword(event.target.value);
                        setPasswordConfirm(event.target.value);
                    }}
                    type="password"
                />
                {authError ? <Paragraph size="small">Invalid password. If you'd like us to reset it, give us a text at (650) 667-1146.</Paragraph> : null}
            </>
        } else if (componentToDisplay === "register") {
            return <>
                <Paragraph textAlign="center" size="small">Create your password.</Paragraph>
                <TextInput
                    icon={<Lock />}
                    placeholder="Enter password"
                    size="small"
                    value={password}
                    onChange={(event) => {setPassword(event.target.value)}}
                    type="password"
                />
                <TextInput
                    icon={<Lock />}
                    placeholder="Type it again"
                    size="small"
                    value={passwordConfirm}
                    onChange={(event) => {setPasswordConfirm(event.target.value)}}
                    type="password"
                />
                {password !== passwordConfirm ? <Paragraph size="small">Passwords don't match.</Paragraph> : null}
            </>
        }
    }, [authError, componentToDisplay, password, passwordConfirm, phoneNumber, secretCode])
    if (cookies.token) {
        return <Redirect to="/"/>;
    }
    return (
        <Box height="100vh" flex="grow" background={{"position":"center","dark":false,"opacity":"strong"}}>
            <Box height="40vh" align="center" justify="center" pad="large">
                <Paragraph>welcome to</Paragraph>
                <Heading>coherence</Heading>
            </Box>
            <Box height="60vh" align="center" justify="between" background={{color: "brand", dark: true}} pad="large">
                <Paragraph color="white" textAlign="center">Peace of mind with your medications is just around the corner.</Paragraph>
                <Box>
                    <Box width="200px" margin={{bottom: "medium", top: "xsmall"}}>
                        {getInputField()}
                    </Box>
                    <Button label="submit" icon={<Login/>} onClick={submitAll} disabled={password !== passwordConfirm}/>
                </Box>
            </Box>
        </Box>
    )
}

export default Intro;