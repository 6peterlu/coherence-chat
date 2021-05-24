import { Box, Button, Heading, Image, Paragraph, TextInput } from "grommet";
import { Clear, Favorite, Info } from "grommet-icons";
import React from "react";
import { landingPageSignup } from "../api";
import AnimatingButton from "../components/AnimatingButton";
import { useHistory } from "react-router-dom"


const LandingPage = ({size}) => {
    console.log(size);
    const [name, setName] = React.useState("");
    const [email, setEmail] = React.useState("");
    const [phoneNumber, setPhoneNumber] = React.useState("");
    const [freeTrialCode, setFreeTrialCode] = React.useState("");
    const [loading, setLoading] = React.useState(false);
    const [submittedForm, setSubmittedForm] = React.useState(false);
    const history = useHistory();

    if (size === "large" || size === "medium") {
        return (
            <Box>
                <Box margin={{horizontal: "large"}} direction="row" justify="between">
                    <Heading size="small">💊 coherence</Heading>
                    <Box direction="row" align="center">
                        <Paragraph margin={{right: "medium"}}>Already have an account?</Paragraph>
                        <Button label="login" onClick={() => {history.push("/login")}}/>
                    </Box>
                </Box>
                <Box align="center" margin={{bottom: "large"}}>
                    <Box direction="row" justify="evenly" align="center" fill="horizontal">
                        <Box direction="column" width="medium">
                            <Heading>Peace of mind with your medication.</Heading>
                            <Paragraph>Your personal medication companion is here at last. No more struggling with annoying alarms. No more wondering whether you've taken a dose or not.</Paragraph>
                            <Button label="Try it out" primary={true} href="#signup"/>
                        </Box>
                        <Box width="medium" direction="row">
                            <Image
                                fit="contain"
                                src="https://uploads-ssl.webflow.com/6033f4ad7e2c0743cd74dfb1/6058b37cab7185d821f3d2df_Coherence%20reminder%20flow-p-800.png"
                                alignSelf="end"
                            />
                        </Box>
                    </Box>
                </Box>
                <Box direction="row" fill="horizontal" justify="around" background="brand" margin={{top: "large"}}>
                    <Box direction="column" align="center" margin="large">
                        <Favorite size="xlarge"/>
                        <Paragraph>Collaborative</Paragraph>
                    </Box>
                    <Box direction="column" align="center" margin="large">
                        <Clear size="xlarge"/>
                        <Paragraph>No apps needed</Paragraph>
                    </Box>
                    <Box direction="column" align="center" margin="large">
                        <Info size="xlarge"/>
                        <Paragraph>Personalized</Paragraph>
                    </Box>
                </Box>
                <Box align="center">
                    <Heading>More than just a reminder.</Heading>
                </Box>
                <Box align="center">
                    <Box width="xlarge">
                        <Image
                            src="https://uploads-ssl.webflow.com/6033f4ad7e2c0743cd74dfb1/607c583233628e615b1d9b38_website%20image.png"
                        />
                    </Box>
                </Box>
                <Box background="brand" id="signup">
                    <Box align="center">
                        <Heading size="small">We can't wait to be a part of your medication journey.</Heading>
                        <Paragraph textAlign="center">Coherence is available now for $6.99 / month. Sign up below for more information!</Paragraph>
                        <Box width="large">
                            <Paragraph>Name</Paragraph>
                            <TextInput placeholder="John" value={name} onChange={(e) => {setName(e.target.value)}}/>
                            <Paragraph>Email address</Paragraph>
                            <TextInput placeholder="john@gmail.com" value={email} onChange={(e) => {setEmail(e.target.value)}}/>
                            <Paragraph>Phone number</Paragraph>
                            <TextInput placeholder="(123)456-7890" value={phoneNumber} onChange={(e) => {setPhoneNumber(e.target.value)}}/>
                            <Paragraph>Free trial code (optional)</Paragraph>
                            <TextInput value={freeTrialCode} onChange={(e) => {setFreeTrialCode(e.target.value)}}/>
                            <Box width="small" alignSelf="center" margin={{vertical: "large"}}>
                                <Button label="sign up" primary={true}/>
                            </Box>
                        </Box>
                    </Box>
                </Box>
            </Box>
        );
    }
    if (size === "small") {
        return (
            <Box>
                <Box margin={{horizontal: "large"}} direction="row" justify="between">
                    <Heading size="small">💊 coherence</Heading>
                    <Box direction="row" align="center">
                        <Button label="login" onClick={() => {history.push("/login")}}/>
                    </Box>
                </Box>
                <Box align="center">
                    <Box direction="column" align="center" fill="horizontal">
                        <Box direction="column" margin="large">
                            <Heading>Peace of mind with your medication.</Heading>
                            <Paragraph>Your personal medication companion is here at last. No more struggling with annoying alarms. No more wondering whether you've taken a dose or not.</Paragraph>
                            <Box align="center">
                                <Button label="Try it out!" primary={true} href="#signup"/>
                            </Box>
                        </Box>
                        <Box direction="row">
                            <Image
                                fit="contain"
                                src="https://uploads-ssl.webflow.com/6033f4ad7e2c0743cd74dfb1/6058b37cab7185d821f3d2df_Coherence%20reminder%20flow-p-800.png"
                            />
                        </Box>
                    </Box>
                </Box>
                <Box background="brand" direction="column">
                    <Box direction="column" align="center" margin="large">
                        <Favorite size="large"/>
                        <Paragraph textAlign="center">Collaborative</Paragraph>
                    </Box>
                    <Box direction="column" align="center" margin="large">
                        <Clear size="large"/>
                        <Paragraph textAlign="center">No apps needed</Paragraph>
                    </Box>
                    <Box direction="column" align="center" margin="large">
                        <Info size="large"/>
                        <Paragraph textAlign="center">Personalized</Paragraph>
                    </Box>
                </Box>
                <Box align="center" margin={{horizontal: "small"}}>
                    <Heading textAlign="center">More than just a reminder.</Heading>
                </Box>
                <Box align="center">
                    <Box width="xlarge">
                        <Image
                            src="https://uploads-ssl.webflow.com/6033f4ad7e2c0743cd74dfb1/607c583233628e615b1d9b38_website%20image.png"
                        />
                    </Box>
                </Box>
                <Box background="brand" id="signup">
                    <Box align="center" margin="small">
                        <Heading size="small" textAlign="center">We can't wait to be a part of your medication journey.</Heading>
                        <Paragraph textAlign="center">Coherence is available now for $6.99 / month. Sign up below for more information!</Paragraph>
                        {submittedForm ?
                            <Box width="large" background="white" round={true} pad="large">
                                <Paragraph textAlign="center">We've received your submission and will reach out to you shortly to complete signup. We can't wait for you to try Coherence!</Paragraph>
                            </Box> :
                            <Box width="large">
                                <Paragraph>Name</Paragraph>
                                <TextInput placeholder="John" value={name} onChange={(e) => {setName(e.target.value)}}/>
                                <Paragraph>Email address</Paragraph>
                                <TextInput placeholder="john@gmail.com" value={email} onChange={(e) => {setEmail(e.target.value)}}/>
                                <Paragraph>Phone number</Paragraph>
                                <TextInput placeholder="(123)456-7890" value={phoneNumber} onChange={(e) => {setPhoneNumber(e.target.value)}}/>
                                <Paragraph>Free trial code (optional)</Paragraph>
                                <TextInput value={freeTrialCode} onChange={(e) => {setFreeTrialCode(e.target.value)}}/>
                                <Box width="small" alignSelf="center" margin={{vertical: "large"}}>
                                    <AnimatingButton
                                        label={
                                            freeTrialCode.toLowerCase() === "vpc30" ? "sign up for 30-day free trial" : freeTrialCode ? "Invalid free trial code" : "sign up"
                                        }
                                        primary={true}
                                        disabled={freeTrialCode !== "" && freeTrialCode.toLowerCase() !== "vpc30"}
                                        color={freeTrialCode && freeTrialCode.toLowerCase() !== "vpc30" ? "status-error" : "status-ok"}
                                        animating={loading}
                                        onClick={async () => {
                                            setLoading(true);
                                            await landingPageSignup(name, email, phoneNumber, freeTrialCode);
                                            setLoading(false);
                                            setSubmittedForm(true);
                                        }}
                                    />
                                </Box>
                            </Box>
                        }
                    </Box>
                </Box>
            </Box>
        );
    }

}

export default LandingPage;