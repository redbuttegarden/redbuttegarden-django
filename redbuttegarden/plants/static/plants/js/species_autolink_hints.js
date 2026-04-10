(function () {
    const PLUGIN_TYPE = "SPECIES_AUTOLINK_HINT";
    let pluginRegistered = false;
    let matcher = null;
    let matcherPromise = null;

    function escapeRegExp(value) {
        return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    }

    function buildMatcher(terms) {
        if (!terms.length) {
            return {
                findRanges() {},
            };
        }

        const pattern = new RegExp(
            `(^|[^\\p{L}\\p{N}_])(${terms
                .map(escapeRegExp)
                .sort(function (left, right) {
                    return right.length - left.length;
                })
                .join("|")})(?![\\p{L}\\p{N}_])`,
            "gu"
        );

        return {
            findRanges(text, callback) {
                pattern.lastIndex = 0;
                let match = null;

                while ((match = pattern.exec(text)) !== null) {
                    const prefix = match[1] || "";
                    const matchedText = match[2];
                    const start = match.index + prefix.length;
                    const end = start + matchedText.length;

                    callback(start, end);

                    if (pattern.lastIndex === match.index) {
                        pattern.lastIndex += 1;
                    }
                }
            },
        };
    }

    function getMatcher(termsUrl) {
        if (!matcherPromise) {
            matcherPromise = window
                .fetch(termsUrl, {
                    credentials: "same-origin",
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                    },
                })
                .then(function (response) {
                    return response.json();
                })
                .then(function (data) {
                    matcher = buildMatcher(data.terms || []);
                    return matcher;
                })
                .catch(function () {
                    matcher = buildMatcher([]);
                    return matcher;
                });
        }

        return matcherPromise;
    }

    function rangeHasEntity(contentBlock, start, end) {
        for (let index = start; index < end; index += 1) {
            if (contentBlock.getEntityAt(index)) {
                return true;
            }
        }

        return false;
    }

    function speciesDecoratorStrategy(contentBlock, callback) {
        if (!matcher || contentBlock.getType() === "code-block") {
            return;
        }

        matcher.findRanges(contentBlock.getText(), function (start, end) {
            if (!rangeHasEntity(contentBlock, start, end)) {
                callback(start, end);
            }
        });
    }

    function speciesDecoratorComponent(props) {
        return window.React.createElement(
            "span",
            {
                className: "species-autolink-hint",
                title: "Will auto-link to a species page on publish",
            },
            props.children
        );
    }

    function registerPlugin() {
        if (
            pluginRegistered ||
            !window.draftail ||
            !window.draftail.registerPlugin ||
            !window.React
        ) {
            return pluginRegistered;
        }

        window.draftail.registerPlugin(
            {
                type: PLUGIN_TYPE,
                decorators: [
                    {
                        strategy: speciesDecoratorStrategy,
                        component: speciesDecoratorComponent,
                    },
                ],
                initialize: function (methods) {
                    getMatcher(this.termsUrl).then(function () {
                        methods.setEditorState(methods.getEditorState());
                    });
                },
            },
            "plugins"
        );

        pluginRegistered = true;
        return true;
    }

    function waitForDraftail() {
        if (registerPlugin()) {
            return;
        }

        window.setTimeout(waitForDraftail, 50);
    }

    waitForDraftail();
})();
