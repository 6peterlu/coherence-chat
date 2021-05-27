import { Box, Heading, Paragraph, Tab, Tabs } from "grommet";
import React from "react";

const Settings = () => {
    return (
        <Box margin="large">
            <Heading size="small">Settings</Heading>
            <Tabs>
                <Tab title="Profile">
                    <Paragraph>timezone</Paragraph>
                </Tab>
                <Tab title="Subscription">
                    <Paragraph>credit cards</Paragraph>
                </Tab>
            </Tabs>
        </Box>
    )
}

export default Settings;