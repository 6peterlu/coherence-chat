import { Box, Button, Heading, Layer, Paragraph, Select, Spinner, Tab, Tabs } from "grommet";
import { Calendar, ContactInfo, Close, Home, FormPreviousLink } from "grommet-icons";
import React from "react";

import { getUserProfile } from "../api";
import { useHistory } from "react-router-dom";
import Payment from "./Payment";

const Settings = () => {
    const history = useHistory();
    const [userProfileData, setUserProfileData] = React.useState(null);
    const [editingField, setEditingField] = React.useState(null);
    React.useEffect(() => {
        const pullUserProfileData = async () => {
            const response = await getUserProfile();
            if (response === null) {
                history.push("/welcome");
                return;
            }
            setUserProfileData({original: response, updated: response});
        }
        pullUserProfileData();
    }, [history]);

    const closeEditingWindow = React.useCallback(() => {
        setUserProfileData({...userProfileData, updated: userProfileData.original});
        setEditingField(null);
    }, [userProfileData]);
    return (
        <Box margin="large">
            <Box align="start">
                <Button
                    icon={<Box direction="row"><FormPreviousLink/><Home/></Box>}
                    label=" "
                    size="small"
                    onClick={() => {history.push("/")}}
                />
            </Box>

            <Heading size="small">Settings</Heading>

            <Tabs alignSelf="stretch">
                <Tab title="Profile" icon={<ContactInfo />}>
                    {userProfileData !== null ?
                        <Box direction="row" align="center" justify="between">
                            <Paragraph>Timezone: {userProfileData.original.timezone}</Paragraph>
                            <Button label="edit" size="small" onClick={() => {setEditingField("timezone")}}/>
                        </Box> : <Spinner />
                    }
                    {editingField === "timezone" ? (
                        <Layer
                            onEsc={closeEditingWindow}
                            onClickOutside={closeEditingWindow}
                            responsive={false}
                        >
                            <Box width="90vw" pad="large">
                                <Box direction="row" justify="between">
                                    <Paragraph size="large">Edit timezone</Paragraph>
                                    <Button icon={<Close />} onClick={closeEditingWindow} />
                                </Box>
                                <Box>
                                    <Select
                                        options={["US/Pacific", "US/Mountain", "US/Central", "US/Eastern"]}
                                        value={userProfileData.updated.timezone}
                                        onChange={({value}) => {
                                            setUserProfileData({...userProfileData, updated: {...userProfileData.updated, timezone: value}});
                                        }}
                                    />
                                </Box>
                            </Box>
                        </Layer>
                    ) : null
                    }
                </Tab>
                <Tab title="Subscription" icon={<Calendar/>}>
                    <Payment />
                </Tab>
            </Tabs>
        </Box>
    )
}

export default Settings;