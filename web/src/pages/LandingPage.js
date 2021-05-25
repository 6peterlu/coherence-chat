import { Anchor, Box, Button, Heading, Image, Paragraph, TextInput } from "grommet";
import { Clear, Favorite, FormNextLink, Info } from "grommet-icons";
import React from "react";
import { landingPageSignup } from "../api";
import AnimatingButton from "../components/AnimatingButton";
import { useHistory } from "react-router-dom"

const heading_copy_1 = "Peace of mind with your medication.";
const heading_copy_2 = "Your personal medication companion is here at last. No more struggling with annoying alarms. No more wondering whether you've taken a dose or not.";
const heading_copy_3 = "Try it out!";

const differentiator_copy_1 = "Here's what makes us different.";
const differentiator_copy_2 = "Collaborative";
const differentiator_copy_3 = "No apps needed";
const differentiator_copy_4 = "Personalized";

const feature_copy_1 = "More than just a reminder.";

const cta_copy_1 = "We can't wait to be a part of your medication journey.";
const cta_copy_2 = "Coherence is available now for $6.99 / month. Sign up below for free information!";


const LandingPage = ({size}) => {
    console.log(size);
    const [name, setName] = React.useState("");
    const [email, setEmail] = React.useState("");
    const [phoneNumber, setPhoneNumber] = React.useState("");
    const [freeTrialCode, setFreeTrialCode] = React.useState("");
    const [loading, setLoading] = React.useState(false);
    const [submittedForm, setSubmittedForm] = React.useState(false);
    const history = useHistory();


    if (size === "large" || size === "xlarge") {
        return (
            <Box>
                <Box margin={{horizontal: "small"}} direction="row" justify="between">
                    <Heading size="small">💊 coherence</Heading>
                    <Box direction="row" align="center">
                        <Paragraph margin={{right: "medium"}}>Already have an account?</Paragraph>
                        <Button label="login" onClick={() => {history.push("/login")}}/>
                    </Box>
                </Box>
                <Box align="center">
                    <Box direction="row" justify="evenly" align="center" fill="horizontal">
                        <Box direction="column" width="medium" margin="small">
                            <Heading size="small">{heading_copy_1}</Heading>
                            <Paragraph>{heading_copy_2}</Paragraph>
                            <Box align="center">
                                <Button label={heading_copy_3} primary={true} href="#signup"/>
                            </Box>
                        </Box>
                        <Box width="medium" direction="row" margin="small">
                            <Image
                                fit="contain"
                                src="https://uploads-ssl.webflow.com/6033f4ad7e2c0743cd74dfb1/6058b37cab7185d821f3d2df_Coherence%20reminder%20flow-p-800.png"
                            />
                        </Box>
                    </Box>
                </Box>
                <Box background="brand" margin={{top: "large"}} align="center">
                    <Heading size="small" textAlign="center">{differentiator_copy_1}</Heading>
                    <Box direction="row" fill="horizontal" justify="around">
                        <Box direction="column" align="center" margin="large">
                            <Favorite size="large"/>
                            <Paragraph textAlign="center">{differentiator_copy_2}</Paragraph>
                        </Box>
                        <Box direction="column" align="center" margin="large">
                            <Clear size="large"/>
                            <Paragraph textAlign="center">{differentiator_copy_3}</Paragraph>
                        </Box>
                        <Box direction="column" align="center" margin="large">
                            <Info size="large"/>
                            <Paragraph textAlign="center">{differentiator_copy_4}</Paragraph>
                        </Box>
                    </Box>
                </Box>
                <Box align="center">
                    <Heading size="small">{feature_copy_1}</Heading>
                </Box>
                <Box align="center">
                    <Box width="xlarge">
                        <Image
                            alignSelf="center"
                            width="90%"
                            src="https://i.ibb.co/G0Q0KK0/Slice-3-3.png"
                        />
                    </Box>
                </Box>
                <Box background="brand" id="signup" align="center" pad="large">
                    <Heading size="small" textAlign="center">{cta_copy_1}</Heading>
                    <Paragraph textAlign="center">{cta_copy_2}</Paragraph>
                    <Box width="large">
                        <Paragraph>Name</Paragraph>
                        <TextInput placeholder="Kari" value={name} onChange={(e) => {setName(e.target.value)}}/>
                        <Paragraph>Email address</Paragraph>
                        <TextInput placeholder="kari@gmail.com" value={email} onChange={(e) => {setEmail(e.target.value)}}/>
                        <Paragraph>Phone number</Paragraph>
                        <TextInput placeholder="(123) 456-7890" value={phoneNumber} onChange={(e) => {setPhoneNumber(e.target.value)}}/>
                        <Paragraph>Free trial code (optional)</Paragraph>
                        <TextInput value={freeTrialCode} onChange={(e) => {setFreeTrialCode(e.target.value)}}/>
                        <Box width="small" alignSelf="center" margin={{vertical: "large"}}>
                            <Button label="sign up" primary={true}/>
                        </Box>
                    </Box>
                </Box>
                <Box direction="row" margin={{horizontal: "large"}} justify="between">
                    <Box>
                        <Paragraph margin={{bottom: "small"}} size="large">Coherence</Paragraph>
                        <Paragraph size="small" margin={{vertical: "none"}}>60 Rausch St #203, San Francisco, CA 94103</Paragraph>
                        <Paragraph size="small" margin={{top: "small", bottom: "none"}}>‪(650) 667-1146‬</Paragraph>
                        <Paragraph size="small" margin={{top: "small"}}>‪contact@hellocoherence.com</Paragraph>
                    </Box>
                    <Box>
                        <Anchor label="Privacy policy" weight="normal" margin={{top: "medium"}} reverse={true} href="/privacy"/>
                        <Paragraph size="small">© Coherence, 2021</Paragraph>
                    </Box>
                </Box>
            </Box>
        );
    }
    if (size === "medium") {
        return (
            <Box>
                <Box margin={{horizontal: "small"}} direction="row" justify="between">
                    <Heading size="small">💊 coherence</Heading>
                    <Box direction="row" align="center">
                        <Button label="login" onClick={() => {history.push("/login")}}/>
                    </Box>
                </Box>
                <Box align="center">
                    <Box direction="row" justify="evenly" align="center" fill="horizontal">
                        <Box direction="column" width="medium" margin="small">
                            <Heading size="small">{heading_copy_1}</Heading>
                            <Paragraph>{heading_copy_2}</Paragraph>
                            <Box align="center">
                                <Button label={heading_copy_3} primary={true} href="#signup"/>
                            </Box>
                        </Box>
                        <Box width="medium" direction="row" margin="small">
                            <Image
                                fit="contain"
                                src="https://uploads-ssl.webflow.com/6033f4ad7e2c0743cd74dfb1/6058b37cab7185d821f3d2df_Coherence%20reminder%20flow-p-800.png"
                            />
                        </Box>
                    </Box>
                </Box>
                <Box background="brand" margin={{top: "large"}} align="center">
                    <Heading size="small" textAlign="center">{differentiator_copy_1}</Heading>
                    <Box direction="row" fill="horizontal" justify="around">
                        <Box direction="column" align="center" margin="large">
                            <Favorite size="large"/>
                            <Paragraph textAlign="center">{differentiator_copy_2}</Paragraph>
                        </Box>
                        <Box direction="column" align="center" margin="large">
                            <Clear size="large"/>
                            <Paragraph textAlign="center">{differentiator_copy_3}</Paragraph>
                        </Box>
                        <Box direction="column" align="center" margin="large">
                            <Info size="large"/>
                            <Paragraph textAlign="center">{differentiator_copy_4}</Paragraph>
                        </Box>
                    </Box>
                </Box>
                <Box align="center">
                    <Heading size="small">{feature_copy_1}</Heading>
                </Box>
                <Box align="center">
                    <Box width="xlarge">
                        <Image
                            alignSelf="center"
                            width="90%"
                            src="https://i.ibb.co/G0Q0KK0/Slice-3-3.png"
                        />
                    </Box>
                </Box>
                <Box background="brand" id="signup" align="center" pad="large">
                    <Heading size="small" textAlign="center">{cta_copy_1}</Heading>
                    <Paragraph textAlign="center">{cta_copy_2}</Paragraph>
                    <Box width="large">
                        <Paragraph>Name</Paragraph>
                        <TextInput placeholder="Kari" value={name} onChange={(e) => {setName(e.target.value)}}/>
                        <Paragraph>Email address</Paragraph>
                        <TextInput placeholder="kari@gmail.com" value={email} onChange={(e) => {setEmail(e.target.value)}}/>
                        <Paragraph>Phone number</Paragraph>
                        <TextInput placeholder="(123) 456-7890" value={phoneNumber} onChange={(e) => {setPhoneNumber(e.target.value)}}/>
                        <Paragraph>Free trial code (optional)</Paragraph>
                        <TextInput value={freeTrialCode} onChange={(e) => {setFreeTrialCode(e.target.value)}}/>
                        <Box width="small" alignSelf="center" margin={{vertical: "large"}}>
                            <Button label="sign up" primary={true}/>
                        </Box>
                    </Box>
                </Box>
                <Box direction="row" margin={{horizontal: "large"}} justify="between">
                    <Box>
                        <Paragraph margin={{bottom: "small"}} size="large">Coherence</Paragraph>
                        <Paragraph size="small" margin={{vertical: "none"}}>60 Rausch St #203, San Francisco, CA 94103</Paragraph>
                        <Paragraph size="small" margin={{top: "small", bottom: "none"}}>‪(650) 667-1146‬</Paragraph>
                        <Paragraph size="small" margin={{top: "small"}}>‪contact@hellocoherence.com</Paragraph>
                    </Box>
                    <Box>
                        <Anchor label="Privacy policy" weight="normal" margin={{top: "medium"}} reverse={true} href="/privacy"/>
                        <Paragraph size="small">© Coherence, 2021</Paragraph>
                    </Box>
                </Box>
            </Box>
        );
    }
    if (size === "small" || size === "xsmall") {
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
                            <Heading>{heading_copy_1}</Heading>
                            <Paragraph>{heading_copy_2}</Paragraph>
                            <Box align="center">
                                <Button label={heading_copy_3} primary={true} href="#signup"/>
                            </Box>
                        </Box>
                        <Box direction="row" width="90%" margin={{bottom: "medium"}}>
                            <Image
                                width="100%"
                                height="100%"
                                src="https://uploads-ssl.webflow.com/6033f4ad7e2c0743cd74dfb1/6058b37cab7185d821f3d2df_Coherence%20reminder%20flow-p-800.png"
                            />
                        </Box>
                    </Box>
                </Box>
                <Box background="brand">
                    <Heading size="medium" textAlign="center">{differentiator_copy_1}</Heading>
                    <Box direction="row">
                        <Box direction="column" align="center" margin="large">
                            <Favorite size="large"/>
                            <Paragraph textAlign="center" size="small">{differentiator_copy_2}</Paragraph>
                        </Box>
                        <Box direction="column" align="center" margin="large">
                            <Clear size="large"/>
                            <Paragraph textAlign="center" size="small">{differentiator_copy_3}</Paragraph>
                        </Box>
                        <Box direction="column" align="center" margin="large">
                            <Info size="large"/>
                            <Paragraph textAlign="center" size="small">{differentiator_copy_4}</Paragraph>
                        </Box>
                    </Box>
                </Box>
                <Box align="center" margin={{horizontal: "small"}}>
                    <Heading textAlign="center">{feature_copy_1}</Heading>
                </Box>
                <Box align="center">
                    <Box width="xlarge">
                        <Image
                            alignSelf="center"
                            width="90%"
                            src="https://i.ibb.co/G0Q0KK0/Slice-3-3.png"
                        />
                    </Box>
                </Box>
                <Box background="brand" id="signup">
                    <Box align="center" margin="small">
                        <Heading size="small" textAlign="center">{cta_copy_1}</Heading>
                        <Paragraph textAlign="center">{cta_copy_2}</Paragraph>
                        {submittedForm ?
                            <Box width="large" background="white" round={true} pad="large">
                                <Paragraph textAlign="center">We've received your submission and will reach out to you shortly to complete signup. We can't wait for you to try Coherence!</Paragraph>
                            </Box> :
                            <Box width="large">
                                <Paragraph>Name</Paragraph>
                                <TextInput placeholder="Kari" value={name} onChange={(e) => {setName(e.target.value)}}/>
                                <Paragraph>Email address</Paragraph>
                                <TextInput placeholder="kari@gmail.com" value={email} onChange={(e) => {setEmail(e.target.value)}}/>
                                <Paragraph>Phone number</Paragraph>
                                <TextInput placeholder="(123) 456-7890" value={phoneNumber} onChange={(e) => {setPhoneNumber(e.target.value)}}/>
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
                <Box direction="row" margin={{horizontal: "large"}} justify="between">
                    <Box>
                        <Paragraph margin={{bottom: "small"}} size="large">Coherence</Paragraph>
                        <Paragraph size="small" margin={{vertical: "none"}}>60 Rausch St #203, San Francisco, CA 94103</Paragraph>
                        <Paragraph size="small" margin={{top: "small", bottom: "none"}}>‪(650) 667-1146‬</Paragraph>
                        <Paragraph size="small" margin={{top: "small"}}>‪contact@hellocoherence.com</Paragraph>
                    </Box>
                    <Box>
                        <Anchor label="Privacy policy" weight="normal" margin={{top: "medium"}} reverse={true} href="/privacy"/>
                        <Paragraph size="small">© Coherence, 2021</Paragraph>
                    </Box>
                </Box>
            </Box>
        );
    }

}

export default LandingPage;