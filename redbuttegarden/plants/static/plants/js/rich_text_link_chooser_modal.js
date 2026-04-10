(function () {
    const SPECIES_CHOOSER_URL = "/admin/species_link_chooser/";
    const COLLECTION_CHOOSER_URL = "/admin/collection_link_chooser/";
    let modalWorkflowPatched = false;
    let pageChooserModalPatched = false;
    let editorLinkTrackingRegistered = false;
    let lastKnownEditorLinkData = null;

    function normalizeAnchorLinkData(anchor) {
        if (!anchor) {
            return null;
        }

        return {
            linkType: anchor.dataset.linktype || anchor.getAttribute("data-linktype"),
            id: anchor.dataset.id || anchor.getAttribute("data-id"),
            url: anchor.getAttribute("href"),
            text: anchor.textContent,
        };
    }

    function rememberEditorLinkData(linkData, reason) {
        if (!linkData || (!linkData.url && !linkData.id && !linkData.linkType)) {
            return;
        }

        lastKnownEditorLinkData = linkData;
    }

    function registerEditorLinkTracking() {
        if (editorLinkTrackingRegistered) {
            return true;
        }

        document.addEventListener(
            "mouseup",
            function (event) {
                const anchor = event.target && event.target.closest
                    ? event.target.closest("a[data-draftail-trigger]")
                    : null;
                if (!anchor) {
                    return;
                }

                rememberEditorLinkData(normalizeAnchorLinkData(anchor), "draftail-trigger-mouseup");
            },
            true,
        );

        editorLinkTrackingRegistered = true;
        return true;
    }

    function isPageChooserUrl(url) {
        return typeof url === "string" && url.indexOf("/admin/choose-page") !== -1;
    }

    function registerModalWorkflowOverride() {
        if (!window.ModalWorkflow || modalWorkflowPatched) {
            return Boolean(window.ModalWorkflow);
        }

        const originalModalWorkflow = window.ModalWorkflow;

        window.ModalWorkflow = function (options) {
            const selectedLinkData = getSelectedEditorLinkData();
            const effectiveSelectedLinkData = selectedLinkData || lastKnownEditorLinkData;
            const inferredPlantLinkType = inferPlantLinkType(effectiveSelectedLinkData);
            const nextOptions = { ...(options || {}) };

            if (isPageChooserUrl(nextOptions.url) && inferredPlantLinkType) {
                const chooserUrl =
                    inferredPlantLinkType === "species"
                        ? SPECIES_CHOOSER_URL
                        : COLLECTION_CHOOSER_URL;
                const selectedId = effectiveSelectedLinkData && effectiveSelectedLinkData.id;
                const linkText =
                    (nextOptions.urlParams && nextOptions.urlParams.link_text) ||
                    (effectiveSelectedLinkData && effectiveSelectedLinkData.text) ||
                    "";

                nextOptions.url = chooserUrl;
                nextOptions.urlParams = {
                    ...(nextOptions.urlParams || {}),
                    q: linkText,
                    selected_id: selectedId,
                    link_text: linkText,
                };
            }

            return originalModalWorkflow.call(this, nextOptions);
        };

        modalWorkflowPatched = true;
        return true;
    }

    function registerPageChooserModalOverride() {
        if (!window.PageChooserModal || pageChooserModalPatched) {
            return Boolean(window.PageChooserModal);
        }

        const OriginalPageChooserModal = window.PageChooserModal;

        window.PageChooserModal = class PlantAwarePageChooserModal extends OriginalPageChooserModal {
            constructor(...args) {
                super(...args);
                this._plantSelectedLinkData = getSelectedEditorLinkData() || lastKnownEditorLinkData;
                this._plantLinkType = inferPlantLinkType(this._plantSelectedLinkData);
            }

            getURL(opts) {
                if (this._plantLinkType === "species") {
                    return SPECIES_CHOOSER_URL;
                }

                if (this._plantLinkType === "collection") {
                    return COLLECTION_CHOOSER_URL;
                }

                return super.getURL(opts);
            }

            getURLParams(opts) {
                const params = super.getURLParams(opts);

                if (!this._plantLinkType) {
                    return params;
                }

                const selectedId = this._plantSelectedLinkData && this._plantSelectedLinkData.id;
                const linkText =
                    params.link_text ||
                    (this._plantSelectedLinkData && this._plantSelectedLinkData.text) ||
                    "";

                const mergedParams = {
                    ...params,
                    q: linkText,
                    selected_id: selectedId,
                    link_text: linkText,
                };

                return mergedParams;
            }
        };

        pageChooserModalPatched = true;
        return true;
    }

    function bindLinkTypeNavigation(modal) {
        window.jQuery("p.link-types a", modal.body).on("click", function () {
            modal.loadUrl(this.href);
            return false;
        });
    }

    function bindResultLinks(modal) {
        window.jQuery("a[data-chooser-modal-choice]", modal.body).on("click", function () {
            modal.loadUrl(this.href);
            return false;
        });

        window.jQuery(".pagination a", modal.body).on("click", function () {
            loadResultsIntoModal(modal, this.href);
            return false;
        });
    }

    function loadResultsIntoModal(modal, url, data) {
        window.jQuery.get(url, data)
            .done(function (html) {
                window.jQuery("#search-results", modal.body).html(html);
                bindResultLinks(modal);
            })
            .fail(function () {});
    }

    function bindSearch(modal) {
        const $form = window.jQuery("form[data-chooser-modal-search]", modal.body);
        if (!$form.length) {
            return;
        }

        let timerId = null;
        const action = $form.attr("action");

        $form.on("submit", function () {
            loadResultsIntoModal(modal, action, $form.serialize());
            return false;
        });

        window.jQuery("#id_q", modal.body).on("input", function () {
            clearTimeout(timerId);
            timerId = setTimeout(function () {
                loadResultsIntoModal(modal, action, $form.serialize());
            }, 200);
        });

        window.jQuery("[data-chooser-modal-search-filter]", modal.body).on("change", function () {
            loadResultsIntoModal(modal, action, $form.serialize());
        });
    }

    function initCustomLinkChooser(modal) {
        bindLinkTypeNavigation(modal);
        bindSearch(modal);
        bindResultLinks(modal);
        window.jQuery("#id_q", modal.body).trigger("focus");
    }

    function inferPlantLinkTypeFromUrl(url) {
        if (typeof url !== "string") {
            return null;
        }

        try {
            url = new window.URL(url, window.location.origin).pathname;
        } catch (_error) {
            // Leave relative paths untouched if URL parsing fails.
        }

        if (/\/plants\/species\/\d+\/?$/.test(url)) {
            return "species";
        }

        if (/\/plants\/collection\/\d+\/?$/.test(url)) {
            return "collection";
        }

        return null;
    }

    function getSelectedEditorLinkData() {
        const selection = window.getSelection && window.getSelection();
        if (!selection || !selection.anchorNode) {
            return null;
        }

        let node = selection.anchorNode;
        if (node.nodeType === Node.TEXT_NODE) {
            node = node.parentNode;
        }

        if (!node || !node.closest) {
            return null;
        }

        const anchor = node.closest("a");
        if (!anchor) {
            return null;
        }

        const linkData = normalizeAnchorLinkData(anchor);
        rememberEditorLinkData(linkData, "selection");
        return linkData;
    }

    function inferPlantLinkType(linkData) {
        if (linkData) {
            const explicitLinkType =
                linkData.linkType || linkData.linktype || linkData["data-linktype"];
            if (explicitLinkType === "species" || explicitLinkType === "collection") {
                return explicitLinkType;
            }

            const inferredFromUrl = inferPlantLinkTypeFromUrl(linkData.url);
            if (inferredFromUrl) {
                return inferredFromUrl;
            }
        }

        let selectedLinkData = getSelectedEditorLinkData();
        if (!selectedLinkData) {
            selectedLinkData = lastKnownEditorLinkData;
            if (!selectedLinkData) {
                return null;
            }
        }

        if (selectedLinkData.linkType === "species" || selectedLinkData.linkType === "collection") {
            return selectedLinkData.linkType;
        }

        return inferPlantLinkTypeFromUrl(selectedLinkData.url);
    }

    function patchDraftailLinkModalSource() {
        if (!window.draftail || !window.draftail.LinkModalWorkflowSource) {
            return false;
        }

        if (window.draftail.LinkModalWorkflowSource.prototype._plantLinksPatched) {
            return true;
        }

        const proto = window.draftail.LinkModalWorkflowSource.prototype;
        const originalGetChooserConfig = proto.getChooserConfig;
        const originalFilterEntityData = proto.filterEntityData;

        proto.getChooserConfig = function (entity, linkText) {
            const chooserUrls = { ...(this.props.entityType?.chooserUrls || {}) };
            const selectedLinkData = getSelectedEditorLinkData();
            const linkData = entity ? entity.getData() : null;
            const mergedLinkData = { ...(selectedLinkData || {}), ...(linkData || {}) };
            const inferredPlantLinkType = inferPlantLinkType(mergedLinkData);

            if (inferredPlantLinkType) {
                const chooserUrl =
                    inferredPlantLinkType === "species"
                        ? chooserUrls.speciesChooser
                        : chooserUrls.collectionChooser;

                if (chooserUrl) {
                    return {
                        url: chooserUrl,
                        urlParams: {
                            page_type: "wagtailcore.page",
                            allow_external_link: true,
                            allow_email_link: true,
                            allow_phone_link: true,
                            allow_anchor_link: true,
                            link_text: linkText,
                            q: linkText,
                            selected_id: mergedLinkData.id,
                        },
                        onload: window.PAGE_CHOOSER_MODAL_ONLOAD_HANDLERS,
                        responses: { pageChosen: this.onChosen },
                    };
                }
            }

            if (mergedLinkData && mergedLinkData.id && typeof mergedLinkData.parentId === "undefined") {
                return originalGetChooserConfig.call(
                    this,
                    {
                        getData: function () {
                            return { ...mergedLinkData, parentId: null };
                        },
                    },
                    linkText,
                );
            }

            return originalGetChooserConfig.call(this, entity, linkText);
        };

        proto.filterEntityData = function (entityData) {
            const filteredData = originalFilterEntityData.call(this, entityData);

            const inferredPlantLinkType = inferPlantLinkType(entityData);
            if (inferredPlantLinkType) {
                filteredData.linkType = inferredPlantLinkType;
                filteredData.parentId = null;
            }

            return filteredData;
        };

        proto._plantLinksPatched = true;
        return true;
    }

    function registerChooserHandlers() {
        if (!window.PAGE_CHOOSER_MODAL_ONLOAD_HANDLERS) {
            return false;
        }

        window.PAGE_CHOOSER_MODAL_ONLOAD_HANDLERS.species_link_choose = initCustomLinkChooser;
        window.PAGE_CHOOSER_MODAL_ONLOAD_HANDLERS.collection_link_choose = initCustomLinkChooser;
        return true;
    }

    let installTimerId = null;
    function installPlantLinkChooserSupport() {
        installTimerId = null;
        const editorLinkTrackingReady = registerEditorLinkTracking();
        const modalWorkflowReady = registerModalWorkflowOverride();
        const pageChooserModalReady = registerPageChooserModalOverride();
        const jqueryReady = Boolean(window.jQuery);
        const handlersReady = registerChooserHandlers();
        const draftailReady = patchDraftailLinkModalSource();

        if (
            !jqueryReady ||
            !handlersReady ||
            !draftailReady ||
            !editorLinkTrackingReady ||
            !modalWorkflowReady ||
            !pageChooserModalReady
        ) {
            if (installTimerId === null) {
                installTimerId = window.setTimeout(installPlantLinkChooserSupport, 100);
            }
        }
    }

    installPlantLinkChooserSupport();
    document.addEventListener("DOMContentLoaded", installPlantLinkChooserSupport);
    window.addEventListener("load", installPlantLinkChooserSupport);
    document.addEventListener("w-draftail:init", installPlantLinkChooserSupport);
})();
