import { Anchor, Box, Button, Heading, Image, Paragraph, TextInput } from "grommet";
import { Clear, Favorite, Info, Star } from "grommet-icons";
import React from "react";
import { landingPageSignup } from "../api";
import AnimatingButton from "../components/AnimatingButton";
import { useHistory, useLocation } from "react-router-dom"

import { Helmet } from "react-helmet";
import { trackLandingPageSignup } from "../analytics";

const heading_copy_1 = "Peace of mind with your medication.";
const heading_copy_2 = "Your personal medication companion is here at last. No more struggling with annoying alarms. No more wondering whether you've taken a dose or not.";
const heading_copy_3 = "Sign up today!";

const differentiator_copy_1 = "Here's what makes us different.";
const differentiator_copy_2 = "Collaborative";
const differentiator_copy_3 = "No apps needed";
const differentiator_copy_4 = "Personalized";
const differentiator_copy_5 = "Coherence works with you to remind you when it's most convenient for you.";
const differentiator_copy_6 = "Coherence will text you at your phone number, no downloads needed.";
const differentiator_copy_7 = "Coherence learns about your habits over time and tailors its texting frequency and style around your preferences.";

const feature_copy_1 = "More than just a reminder.";

const reviews_copy_1 = "See what others are saying.";
const reviews_copy_2 = "Cheryl";
const reviews_copy_3 = "\"I love it, I love it, I love it. I was previously using my phone calendar to remind me and that was not helping at all. I've remembered all of my doses on Coherence.\"";
const reviews_copy_4 = "Andie";
const reviews_copy_5 = "\"Coherence has helped me track my medicine for months now — I am indebted to its texting function for keeping myself more accountable. The kind messaging and gentle reminders are incredibly sweet; I don’t feel like I’m talking to a sterile robot but someone who is genuinely invested in my health.\"";
const reviews_copy_6 = "Jeanette";
const reviews_copy_7 = "\"I find Coherence very uplifting, and it makes it so easy for me to stick to my critical medications.\"";



const cta_copy_1 = "We can't wait to be a part of your medication journey.";
const cta_copy_2 = "Coherence is available now for $6.99 / month. Sign up below for free information!";
const cta_copy_3 = "Sign up below to try Coherence free for 30 days. Cancel anytime.";


const LandingPage = ({size}) => {
    console.log(size);
    const [name, setName] = React.useState("");
    const [email, setEmail] = React.useState("");
    const [phoneNumber, setPhoneNumber] = React.useState("");
    const [freeTrialCode, setFreeTrialCode] = React.useState("");
    const [loading, setLoading] = React.useState(false);
    const [submittedForm, setSubmittedForm] = React.useState(false);
    const history = useHistory();
    const location = useLocation();
    const enableFreeTrial = location.pathname === "/signup";

    const formButtonState = React.useMemo(() => {
        if (!name) {
            return {disabled: true, text: "Name field empty."}
        }
        if (!email) {
            return {disabled: true, text: "Email field empty."}
        }
        const emailRegex = /.*@.*\..*/;
        if (!emailRegex.test(email)) {
            return { disabled: true, text: "Email format is invalid."}
        }
        if (!phoneNumber) {
            return { disabled: true, text: "Phone number field empty." }
        }
        const nonDigitRegex = /\D/g;
        if (phoneNumber.replace(nonDigitRegex, "").length !== 10) {
            return { disabled: true, text: "Phone number is not 10 digits."}
        }
        if (freeTrialCode) {
            const freeTrialCodes = ["vpc30", "june30"]
            if (!freeTrialCodes.includes(freeTrialCode.toLowerCase())) {
                return { disabled: true, text: "Invalid trial code."}
            } else {
                return { disabled: false, text: "Get your free 30-day trial!"}
            }

        }
        return {disabled: false, text: "Sign up"};
    }, [email, freeTrialCode, name, phoneNumber])


    if (size === "large" || size === "xlarge") {
        return (
            <Box>
                <Helmet>
                    <meta name="title" content="Coherence - an intelligent medication companion, just for you."/>
                    <meta name="description" content="Coherence is an AI companion designed to help you stick to your medications. Get set up in minutes. Available now."/>
                </Helmet>
                <Box pad={{horizontal: "large"}} direction="row" justify="between" background="brand">
                    <Heading size="small">💊 coherence</Heading>
                    <Box direction="row" align="center">
                        <Paragraph margin={{right: "medium"}}>Already have an account?</Paragraph>
                        <Button label="login" onClick={() => {history.push("/login")}}/>
                    </Box>
                </Box>
                <Box align="center">
                    <Box direction="row" justify="evenly" align="center" fill="horizontal">
                        <Box direction="column" width="medium" margin="small">
                            <Heading size="medium" color="status-warning">{heading_copy_1}</Heading>
                            <Paragraph>{heading_copy_2}</Paragraph>
                            <Box align="center">
                                <Button label={heading_copy_3} primary={true} href="#signup" color="status-warning"/>
                            </Box>
                        </Box>
                        <Box width="medium" direction="row" margin="small" pad="large">
                            <Image
                                fit="contain"
                                src="https://i.ibb.co/pytvBPR/Frame-4-1.png"
                            />
                        </Box>
                    </Box>
                </Box>
                <Box background="brand" margin={{top: "large", bottom: "none"}} align="center">
                    <Heading size="small" textAlign="center" color="status-warning">{differentiator_copy_1}</Heading>
                    <Box direction="row" fill="horizontal" justify="around">
                        <Box direction="column" align="center" margin={{horizontal: "large", vertical: "small"}}>
                            <Favorite size="large"/>
                            <Paragraph textAlign="center" size="large">{differentiator_copy_2}</Paragraph>
                            <Paragraph size="small" textAlign="center">{differentiator_copy_5}</Paragraph>
                        </Box>
                        <Box direction="column" align="center" margin={{horizontal: "large", vertical: "small"}}>
                            <Clear size="large"/>
                            <Paragraph textAlign="center" size="large">{differentiator_copy_3}</Paragraph>
                            <Paragraph size="small" textAlign="center">{differentiator_copy_6}</Paragraph>
                        </Box>
                        <Box direction="column" align="center" margin={{horizontal: "large", vertical: "small"}}>
                            <Info size="large"/>
                            <Paragraph textAlign="center" size="large">{differentiator_copy_4}</Paragraph>
                            <Paragraph size="small" textAlign="center">{differentiator_copy_7}</Paragraph>
                        </Box>
                    </Box>
                </Box>
                <Box align="center" margin={{bottom: "medium"}}>
                    <Heading size="small" color="status-warning">{feature_copy_1}</Heading>
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
                <Box background="brand" align="center">
                    <Heading size="small" textAlign="center" color="status-warning">{reviews_copy_1}</Heading>
                    <Box justify="between" direction="row" gap="large" margin={{ horizontal: "large" }}>
                        <Box width="33%" align="center">
                            <Box direction="row" align="center">
                                <Paragraph size="large">{reviews_copy_2}</Paragraph>
                                <Box direction="row" margin={{left: "small"}} wrap={true}>
                                    <Star/>
                                    <Star/>
                                    <Star/>
                                    <Star/>
                                    <Star/>
                                </Box>
                            </Box>
                            <Paragraph textAlign="center">{reviews_copy_3}</Paragraph>
                        </Box>
                        <Box width="33%" align="center">
                            <Box direction="row" align="center">
                                <Paragraph size="large">{reviews_copy_4}</Paragraph>
                                <Box direction="row" margin={{left: "small"}} wrap={true}>
                                    <Star/>
                                    <Star/>
                                    <Star/>
                                    <Star/>
                                    <Star/>
                                </Box>
                            </Box>
                            <Paragraph textAlign="center">{reviews_copy_5}</Paragraph>
                        </Box>
                        <Box width="33%" align="center">
                            <Box direction="row" align="center">
                                <Paragraph size="large">{reviews_copy_6}</Paragraph>
                                <Box direction="row" margin={{left: "small"}} wrap={true}>
                                    <Star/>
                                    <Star/>
                                    <Star/>
                                    <Star/>
                                    <Star/>
                                </Box>
                            </Box>
                            <Paragraph textAlign="center">{reviews_copy_7}</Paragraph>
                        </Box>
                    </Box>
                </Box>
                <Box id="signup" align="center" pad="large">
                    <Heading size="small" textAlign="center" color="status-warning">{cta_copy_1}</Heading>
                    <Paragraph textAlign="center">{enableFreeTrial ? cta_copy_3 : cta_copy_2}</Paragraph>
                    {submittedForm ?
                        <Box width="large" background="white" round={true} pad="large" align="center">
                            <Paragraph textAlign="center">We've received your submission and will reach out to you shortly to complete signup. We can't wait for you to try Coherence!</Paragraph>
                        </Box> :
                        <Box width="medium">
                            <Paragraph>Name</Paragraph>
                            <TextInput placeholder="Kari" value={name} onChange={(e) => {setName(e.target.value)}}/>
                            <Paragraph>Email address</Paragraph>
                            <TextInput placeholder="kari@gmail.com" value={email} onChange={(e) => {setEmail(e.target.value)}}/>
                            <Paragraph>Phone number</Paragraph>
                            <TextInput placeholder="(123) 456-7890" value={phoneNumber} onChange={(e) => {setPhoneNumber(e.target.value)}}/>
                            {!enableFreeTrial ?
                                <>
                                    <Paragraph>Free trial code (optional)</Paragraph>
                                    <TextInput value={freeTrialCode} onChange={(e) => {setFreeTrialCode(e.target.value)}}/>
                                </> : null
                            }
                            <Box width="small" alignSelf="center" margin={{vertical: "large"}}>
                                <AnimatingButton
                                    label={formButtonState.text}
                                    primary={true}
                                    disabled={formButtonState.disabled}
                                    color={formButtonState.disabled ? "status-error" : "status-ok"}
                                    animating={loading}
                                    onClick={async () => {
                                        setLoading(true);
                                        await landingPageSignup(name, email, phoneNumber, enableFreeTrial ? "google" : freeTrialCode);
                                        trackLandingPageSignup(phoneNumber);
                                        setLoading(false);
                                        setSubmittedForm(true);
                                    }}
                                />
                            </Box>
                        </Box>
                    }
                </Box>
                <Box direction="row" pad={{horizontal: "large"}} justify="between" background="brand">
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
                <Helmet>
                    <meta name="title" content="Coherence - an intelligent medication companion, just for you."/>
                    <meta name="description" content="Coherence is an AI companion designed to help you stick to your medications. Get set up in minutes. Available now."/>
                </Helmet>
                <Box pad={{horizontal: "medium"}} direction="row" justify="between" background="brand">
                    <Heading size="small">💊 coherence</Heading>
                    <Box direction="row" align="center">
                        <Button label="login" onClick={() => {history.push("/login")}}/>
                    </Box>
                </Box>
                <Box align="center">
                    <Box direction="row" justify="evenly" align="center" fill="horizontal">
                        <Box direction="column" width="medium" margin="small">
                            <Heading size="small" color="status-warning">{heading_copy_1}</Heading>
                            <Paragraph>{heading_copy_2}</Paragraph>
                            <Box align="center">
                                <Button label={heading_copy_3} primary={true} href="#signup" color="status-warning"/>
                            </Box>
                        </Box>
                        <Box width="medium" direction="row" margin="small" height="100vh" pad={{horizontal: "large"}}>
                            <Image
                                fit="contain"
                                src="https://i.ibb.co/pytvBPR/Frame-4-1.png"
                                width="100%"
                            />
                        </Box>
                    </Box>
                </Box>
                <Box background="brand" margin={{top: "small"}} align="center">
                    <Heading size="small" textAlign="center" color="status-warning">{differentiator_copy_1}</Heading>
                    <Box direction="row" fill="horizontal" justify="around">
                        <Box direction="column" align="center" margin="large">
                            <Favorite size="large"/>
                            <Paragraph textAlign="center">{differentiator_copy_2}</Paragraph>
                            <Paragraph size="small" textAlign="center">{differentiator_copy_5}</Paragraph>
                        </Box>
                        <Box direction="column" align="center" margin="large">
                            <Clear size="large"/>
                            <Paragraph textAlign="center">{differentiator_copy_3}</Paragraph>
                            <Paragraph size="small" textAlign="center">{differentiator_copy_6}</Paragraph>
                        </Box>
                        <Box direction="column" align="center" margin="large">
                            <Info size="large"/>
                            <Paragraph textAlign="center">{differentiator_copy_4}</Paragraph>
                            <Paragraph size="small" textAlign="center">{differentiator_copy_7}</Paragraph>
                        </Box>
                    </Box>
                </Box>
                <Box align="center">
                    <Heading size="small" color="status-warning">{feature_copy_1}</Heading>
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
                <Box background="brand" align="center">
                    <Heading size="small" textAlign="center" color="status-warning">{reviews_copy_1}</Heading>
                    <Box justify="between" direction="row" gap="large" margin={{ horizontal: "large" }}>
                        <Box width="33%" align="center">
                            <Box align="center">
                                <Paragraph size="large">{reviews_copy_2}</Paragraph>
                                <Box direction="row" margin={{left: "small"}} wrap={true}>
                                    <Star/>
                                    <Star/>
                                    <Star/>
                                    <Star/>
                                    <Star/>
                                </Box>
                            </Box>
                            <Paragraph textAlign="center">{reviews_copy_3}</Paragraph>
                        </Box>
                        <Box width="33%" align="center">
                            <Box align="center">
                                <Paragraph size="large">{reviews_copy_4}</Paragraph>
                                <Box direction="row" margin={{left: "small"}} wrap={true}>
                                    <Star/>
                                    <Star/>
                                    <Star/>
                                    <Star/>
                                    <Star/>
                                </Box>
                            </Box>
                            <Paragraph textAlign="center">{reviews_copy_5}</Paragraph>
                        </Box>
                        <Box width="33%" align="center">
                            <Box align="center">
                                <Paragraph size="large">{reviews_copy_6}</Paragraph>
                                <Box direction="row" margin={{left: "small"}} wrap={true}>
                                    <Star/>
                                    <Star/>
                                    <Star/>
                                    <Star/>
                                    <Star/>
                                </Box>
                            </Box>
                            <Paragraph textAlign="center">{reviews_copy_7}</Paragraph>
                        </Box>
                    </Box>
                </Box>
                <Box id="signup" align="center" pad="large">
                    <Heading size="small" textAlign="center" color="status-warning">{cta_copy_1}</Heading>
                    <Paragraph textAlign="center">{enableFreeTrial ? cta_copy_3 : cta_copy_2}</Paragraph>
                    {submittedForm ?
                        <Box width="large" background="white" round={true} pad="large" align="center">
                            <Paragraph textAlign="center">We've received your submission and will reach out to you shortly to complete signup. We can't wait for you to try Coherence!</Paragraph>
                        </Box> :
                        <Box width="large">
                            <Paragraph>Name</Paragraph>
                            <TextInput placeholder="Kari" value={name} onChange={(e) => {setName(e.target.value)}}/>
                            <Paragraph>Email address</Paragraph>
                            <TextInput placeholder="kari@gmail.com" value={email} onChange={(e) => {setEmail(e.target.value)}}/>
                            <Paragraph>Phone number</Paragraph>
                            <TextInput placeholder="(123) 456-7890" value={phoneNumber} onChange={(e) => {setPhoneNumber(e.target.value)}}/>
                            {!enableFreeTrial ?
                                <>
                                    <Paragraph>Free trial code (optional)</Paragraph>
                                    <TextInput value={freeTrialCode} onChange={(e) => {setFreeTrialCode(e.target.value)}}/>
                                </> : null
                            }
                            <Box width="small" alignSelf="center" margin={{vertical: "large"}}>
                                <AnimatingButton
                                    label={formButtonState.text}
                                    primary={true}
                                    disabled={formButtonState.disabled}
                                    color={formButtonState.disabled ? "status-error" : "status-ok"}
                                    animating={loading}
                                    onClick={async () => {
                                        setLoading(true);
                                        await landingPageSignup(name, email, phoneNumber, enableFreeTrial ? "google" : freeTrialCode);
                                        trackLandingPageSignup(phoneNumber);
                                        setLoading(false);
                                        setSubmittedForm(true);
                                    }}
                                />
                            </Box>
                        </Box>
                    }
                </Box>
                <Box background="brand" direction="row" pad={{horizontal: "large"}} justify="between">
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
                <Helmet>
                    <meta name="title" content="Coherence - an intelligent medication companion, just for you."/>
                    <meta name="description" content="Coherence is an AI companion designed to help you stick to your medications. Get set up in minutes. Available now."/>
                </Helmet>
                <Box pad={{horizontal: "large"}} direction="row" justify="between" background="brand">
                    <Heading size="small">💊 coherence</Heading>
                    <Box direction="row" align="center">
                        <Button label="login" onClick={() => {history.push("/login")}}/>
                    </Box>
                </Box>
                <Box align="center">
                    <Box direction="column" align="center" fill="horizontal">
                        <Box direction="column" margin="large">
                            <Heading color="status-warning">{heading_copy_1}</Heading>
                            <Paragraph>{heading_copy_2}</Paragraph>
                            <Box align="center">
                                <Button label={heading_copy_3} primary={true} href="#signup" color="status-warning"/>
                            </Box>
                        </Box>
                        <Box direction="row" width="70%" height="100%" margin={{bottom: "medium"}}>
                            <Image
                                width="100%"
                                height="100%"
                                src="https://i.ibb.co/pytvBPR/Frame-4-1.png"
                            />
                        </Box>
                    </Box>
                </Box>
                <Box background="brand">
                    <Heading size="small" textAlign="center" color="status-warning">{differentiator_copy_1}</Heading>
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
                    <Heading textAlign="center" color="status-warning" size="small">{feature_copy_1}</Heading>
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
                <Box background="brand" align="center">
                    <Heading size="small" textAlign="center" color="status-warning">{reviews_copy_1}</Heading>
                    <Box gap="medium" margin={{ horizontal: "medium" }} align="center">
                        <Box align="center">
                            <Box align="center">
                                <Paragraph size="large">{reviews_copy_2}</Paragraph>
                                <Box direction="row" margin={{left: "small"}} wrap={true}>
                                    <Star/>
                                    <Star/>
                                    <Star/>
                                    <Star/>
                                    <Star/>
                                </Box>
                            </Box>
                            <Paragraph textAlign="center">{reviews_copy_3}</Paragraph>
                        </Box>
                        <Box align="center">
                            <Box align="center">
                                <Paragraph size="large">{reviews_copy_4}</Paragraph>
                                <Box direction="row" margin={{left: "small"}} wrap={true}>
                                    <Star/>
                                    <Star/>
                                    <Star/>
                                    <Star/>
                                    <Star/>
                                </Box>
                            </Box>
                            <Paragraph textAlign="center">{reviews_copy_5}</Paragraph>
                        </Box>
                        <Box align="center">
                            <Box align="center">
                                <Paragraph size="large">{reviews_copy_6}</Paragraph>
                                <Box direction="row" margin={{left: "small"}} wrap={true}>
                                    <Star/>
                                    <Star/>
                                    <Star/>
                                    <Star/>
                                    <Star/>
                                </Box>
                            </Box>
                            <Paragraph textAlign="center">{reviews_copy_7}</Paragraph>
                        </Box>
                    </Box>
                </Box>
                <Box id="signup">
                    <Box align="center" margin="small">
                        <Heading size="small" textAlign="center" color="status-warning">{cta_copy_1}</Heading>
                        <Paragraph textAlign="center">{enableFreeTrial ? cta_copy_3 : cta_copy_2}</Paragraph>
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
                                {!enableFreeTrial ?
                                    <>
                                        <Paragraph>Free trial code (optional)</Paragraph>
                                        <TextInput value={freeTrialCode} onChange={(e) => {setFreeTrialCode(e.target.value)}}/>
                                    </> : null
                                }
                                <Box width="small" alignSelf="center" margin={{vertical: "large"}}>
                                    <AnimatingButton
                                        label={formButtonState.text}
                                        primary={true}
                                        disabled={formButtonState.disabled}
                                        color={formButtonState.disabled ? "status-error" : "status-ok"}
                                        animating={loading}
                                        onClick={async () => {
                                            setLoading(true);
                                            await landingPageSignup(name, email, phoneNumber, enableFreeTrial ? "google" : freeTrialCode);
                                            trackLandingPageSignup(phoneNumber);
                                            setLoading(false);
                                            setSubmittedForm(true);
                                        }}
                                    />
                                </Box>
                            </Box>
                        }
                    </Box>
                </Box>
                <Box background="brand" direction="row" pad={{horizontal: "large"}} justify="between">
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