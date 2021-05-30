import { Box, Button, Heading, Layer, Paragraph, Select, Spinner, Tab, Tabs, TextInput } from "grommet";
import { Calendar, ContactInfo, Close, Home, FormPreviousLink } from "grommet-icons";
import React from "react";

import { getUserProfile, updateUserPassword, updateUserTimezone } from "../api";
import { useHistory } from "react-router-dom";
import Payment from "./Payment";
import AnimatingButton from "../components/AnimatingButton";

const Settings = () => {
    const history = useHistory();
    const [userProfileData, setUserProfileData] = React.useState(null);
    const [editingField, setEditingField] = React.useState(null);
    const [animating, setAnimating] = React.useState(false);
    const [newPassword1, setNewPassword1] = React.useState("");
    const [newPassword2, setNewPassword2] = React.useState("");
    const closeEditingWindow = React.useCallback(() => {
        setUserProfileData({...userProfileData, updated: userProfileData.original});
        setEditingField(null);
    }, [userProfileData]);
    const pullUserProfileData = React.useCallback(async () => {
        const response = await getUserProfile();
        if (response === null) {
            history.push("/welcome");
            return;
        }
        setUserProfileData({original: response, updated: response});
        setEditingField(null);
        setAnimating(false);
    },[history])
    React.useEffect(() => {
        pullUserProfileData();
    }, [history, pullUserProfileData]);
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
                        <Box>
                            <Box direction="row" align="center" justify="between">
                                <Paragraph>Timezone: {userProfileData.original.timezone}</Paragraph>
                                <Button label="edit" size="small" onClick={() => {setEditingField("timezone")}}/>
                            </Box>
                            <Box direction="row" align="center" justify="between">
                                <Paragraph>Password: ••••••••</Paragraph>
                                <Button label="edit" size="small" onClick={() => {setEditingField("password")}}/>
                            </Box>
                        </Box>
                        : <Spinner />
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
                                <Box align="center">
                                    <Select
                                        options={["US/Pacific", "US/Mountain", "US/Central", "US/Eastern"]}
                                        value={userProfileData.updated.timezone}
                                        onChange={({value}) => {
                                            setUserProfileData({...userProfileData, updated: {...userProfileData.updated, timezone: value}});
                                        }}
                                    />
                                    <Box margin={{vertical: "medium"}}>
                                        <AnimatingButton
                                            animating={animating}
                                            label="Update timezone"
                                            onClick={async () => {
                                                setAnimating(true);
                                                await updateUserTimezone(userProfileData.updated.timezone);
                                                await pullUserProfileData();
                                            }}
                                        />
                                    </Box>
                                    <Paragraph size="small">
                                        Note: Your dose window times will automatically be transferred to the new timezone.
                                    </Paragraph>
                                </Box>
                            </Box>
                        </Layer>
                    ) : null
                    }
                    {editingField === "password" ? (
                        <Layer
                            onEsc={closeEditingWindow}
                            onClickOutside={closeEditingWindow}
                            responsive={false}
                        >
                            <Box width="90vw" pad="large">
                                <Box direction="row" justify="between">
                                    <Paragraph size="large">Update password</Paragraph>
                                    <Button icon={<Close />} onClick={closeEditingWindow} />
                                </Box>
                                <Paragraph>Enter new password twice for validation.</Paragraph>
                                <Box align="center">
                                    <TextInput type="password" placeholder="••••••••" value={newPassword1} onChange={(event) => {setNewPassword1(event.target.value)}}/>
                                    <TextInput type="password" placeholder="••••••••" value={newPassword2} onChange={(event) => {setNewPassword2(event.target.value)}}/>
                                    <Box margin={{vertical: "medium"}}>
                                        <AnimatingButton
                                            animating={animating}
                                            label="Update password"
                                            onClick={async () => {
                                                setAnimating(true);
                                                await updateUserPassword(newPassword1);
                                                await pullUserProfileData();
                                                setNewPassword1("");
                                                setNewPassword2("");
                                            }}
                                            disabled={ !newPassword1 || newPassword1 !== newPassword2 }
                                        />
                                    </Box>
                                </Box>
                            </Box>
                        </Layer>
                    ) : null
                    }
                </Tab>
                {userProfileData &&
                !userProfileData.original.early_adopter &&
                userProfileData.original.onboarding_type === "standard" ? (<Tab title="Subscription" icon={<Calendar/>}>
                    <Payment />
                </Tab>) : null}
            </Tabs>
        </Box>
    )
}

export default Settings;