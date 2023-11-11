window.addEventListener('DOMContentLoaded', (event) => {
    CometChatWidget.init({
        "appID": APP_ID,
        "appRegion": APP_REGION,
        "authKey": AUTH_KEY
    }).then((response) => {
        /**
         * Create user once initialization is successful
         */
        const user = new CometChatWidget.CometChat.User(USER_ID);
        user.setName(USER_NAME);
        CometChatWidget.createOrUpdateUser(user).then((user) => {

            // Proceed with user login
            CometChatWidget.login({
                uid: USER_ID,
            }).then(response => {
                CometChatWidget.launch({
                    "widgetID": WIDGET_ID,
                    "target": "#cometchat",
                    "roundedCorners": "true",
                    "height": "600px",
                    "width": "800px",
                    "defaultID": "cdc_tickets", //default UID (user) or GUID (group) to show,
                    "defaultType": "group" //user or group
                });
            }, error => {
                console.log("User login failed with error:", error);
                //Check the reason for error and take appropriate action.
            });
        }, error => {
            console.log("Initialization failed with error:", error);
            //Check the reason for error and take appropriate action.
        });
    });
});
