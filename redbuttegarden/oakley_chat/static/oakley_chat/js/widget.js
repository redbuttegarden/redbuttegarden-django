(function () {
    const widget = document.getElementById("oakley-chat-widget");
    if (!widget) {
        return;
    }

    const sendUrl = widget.dataset.sendUrl;
    const csrfToken = widget.dataset.csrfToken;
    const toggle = widget.querySelector(".oakley-chat__toggle");
    const panel = document.getElementById("oakley-chat-panel");
    const form = document.getElementById("oakley-chat-form");
    const input = document.getElementById("oakley-chat-input");
    const messages = document.getElementById("oakley-chat-messages");
    const typing = document.getElementById("oakley-chat-typing");
    const prompts = document.getElementById("oakley-chat-prompts");
    const submitButton = form.querySelector("button[type='submit']");

    function escapeHtml(value) {
        const div = document.createElement("div");
        div.textContent = value;
        return div.innerHTML;
    }

    function scrollToBottom() {
        messages.scrollTop = messages.scrollHeight;
    }

    function appendMessage(author, content, options) {
        const settings = options || {};
        const wrapper = document.createElement("div");
        wrapper.className = `oakley-chat__message oakley-chat__message--${settings.kind || "agent"}`;

        const authorLabel = document.createElement("span");
        authorLabel.className = "oakley-chat__author";
        authorLabel.textContent = author;

        const bubble = document.createElement("div");
        bubble.className = "oakley-chat__bubble";
        bubble.innerHTML = settings.html ? content : `<p>${escapeHtml(content)}</p>`;

        wrapper.appendChild(authorLabel);
        wrapper.appendChild(bubble);
        messages.appendChild(wrapper);
        scrollToBottom();
    }

    function renderPrompts(items) {
        prompts.innerHTML = "";

        (items || []).forEach(function (prompt) {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "oakley-chat__prompt";
            button.textContent = prompt;
            button.addEventListener("click", function () {
                sendMessage(prompt);
            });
            prompts.appendChild(button);
        });
    }

    function setPendingState(isPending) {
        typing.hidden = !isPending;
        input.disabled = isPending;
        submitButton.disabled = isPending;
        prompts.querySelectorAll("button").forEach(function (button) {
            button.disabled = isPending;
        });
        if (!isPending) {
            input.focus();
        }
        scrollToBottom();
    }

    function shouldShowOfficialSiteLookupStatus(chatInput) {
        return /\b(member\s+pre-?sale|pre-?sale|public\s+on-?sale|public\s+sale|on-?sale|tickets?\s+(?:go|are)\s+on sale|wave\s+one|wave\s+two|wave\s+1|wave\s+2|which\s+wave|what\s+wave|part\s+of\s+wave)\b/i.test(chatInput);
    }

    async function sendMessage(rawMessage) {
        const message = (rawMessage || "").trim();
        if (!message || !sendUrl) {
            return;
        }

        appendMessage("You", message, { kind: "user", html: false });
        if (shouldShowOfficialSiteLookupStatus(message)) {
            appendMessage(
                "Oakley",
                "I&apos;m checking the official Red Butte Garden website for that. This may take a little longer.",
                { kind: "agent", html: true }
            );
        }

        input.value = "";
        renderPrompts([]);
        setPendingState(true);

        try {
            const response = await fetch(sendUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "X-CSRFToken": csrfToken,
                    "X-Requested-With": "XMLHttpRequest"
                },
                body: new URLSearchParams({ message: message }).toString()
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || "The Oakley chatbot service is unavailable right now.");
            }

            appendMessage("Oakley", data.reply_html || "<p>No response</p>", {
                kind: "agent",
                html: true
            });
            renderPrompts(data.suggested_prompts || []);
        } catch (error) {
            appendMessage("Oakley", error.message, { kind: "agent", html: false });
        } finally {
            setPendingState(false);
        }
    }

    toggle.addEventListener("click", function () {
        const isExpanded = toggle.getAttribute("aria-expanded") === "true";
        toggle.setAttribute("aria-expanded", String(!isExpanded));
        panel.hidden = isExpanded;
        if (!isExpanded) {
            input.focus();
            scrollToBottom();
        }
    });

    form.addEventListener("submit", function (event) {
        event.preventDefault();
        sendMessage(input.value);
    });
})();
