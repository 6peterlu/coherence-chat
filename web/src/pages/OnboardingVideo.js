import React from "react";
import Youtube from "react-youtube";
import { Box, Heading, Paragraph } from "grommet";

const OnboardingVideo = () => {
    const opts = {
        width: "100%",
        playerVars: {
            modestbranding: 1
        }
    }
    return <Box align="center" background="brand" height="100vh" fill="horizontal" pad="medium">
        <Heading size="small">Welcome to Coherence!</Heading>
        <Paragraph textAlign="center">Watch the video below to learn more about our product features.</Paragraph>
        <Box width="large">
            <Youtube
                videoId="2kH0-IE1QvU"
                opts={opts}
            />
        </Box>
        <Paragraph textAlign="center">When you're done, head back to your texts and let us know how many dose windows you'd like to set up.</Paragraph>
    </Box>
}

export default OnboardingVideo;