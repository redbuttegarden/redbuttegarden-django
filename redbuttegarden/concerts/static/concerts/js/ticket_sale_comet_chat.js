const frame = (async () => {
    // DSChatSDK construction accepts two parameters:
    // 1. Chat Room Id
    // 2. ID of the iFrame tag
    // 3. Dead Simple Chat Public API Key.
    const sdk = new DSChatSDK("Q53Td0Ekr", "chat-frame", "pub_5361323747657377594a38586c6859544155494b6c394d655f503448457a534d37526c67384f53714933626737412d59");
    // Call the connect method to connect the SDK to the Chat iFrame.
    await sdk.connect();

    /**
     * Calling the Join Method to Join the Chat Room
     */
    await sdk.joinRoom({
        uniqueUserIdentifier: USER_ID
    });
})();