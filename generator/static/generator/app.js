// Simple jQuery AJAX for the AI Campaign Brief Generator.
$(function () {
    "use strict";

    // Read the CSRF cookie so Django accepts our POST (CSRF stays enabled).
    function getCookie(name) {
        var match = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
        return match ? decodeURIComponent(match.pop()) : "";
    }

    var $form = $("#brief-form");
    var $btn = $("#submit-btn");

    // --- UI helpers ----------------------------------------------------------
    function showError(message) {
        $("#error").text(message).prop("hidden", false);
    }
    function hide(selector) { $(selector).prop("hidden", true); }
    function show(selector) { $(selector).prop("hidden", false); }

    function setLoading(isLoading) {
        $btn.prop("disabled", isLoading).text(isLoading ? "Generating…" : "Generate Brief");
        if (isLoading) {
            hide("#error"); hide("#placeholder"); hide("#result"); show("#loading");
        } else {
            hide("#loading");
        }
    }

    // Render a finished brief. Always use .text() so model output can't inject HTML.
    function renderResult(data) {
        $("#brief").text(data.brief);

        var $angles = $("#angles").empty();
        $.each(data.angles, function (_, angle) { $angles.append($("<li>").text(angle)); });

        var $criteria = $("#criteria").empty();
        $.each(data.criteria, function (_, item) { $criteria.append($("<li>").text(item)); });

        var m = data.metrics || {};
        $("#metrics").empty().append(
            $("<span class='metric'>").html("Latency: <strong>" + m.latency_ms + " ms</strong>"),
            $("<span class='metric'>").html("Tokens: <strong>" + m.total_tokens + "</strong>"),
            $("<span class='metric'>").html("Est. cost: <strong>$" + Number(m.estimated_cost_usd).toFixed(6) + "</strong>"),
            $("<span class='metric'>").html("Model: <strong>" + m.model + "</strong>")
        );

        show("#result");
    }

    // --- Events --------------------------------------------------------------
    // Copy the brief text to the clipboard.
    $("#copy-btn").on("click", function () {
        var text = $("#brief").text();
        var $b = $(this);
        navigator.clipboard.writeText(text).then(function () {
            $b.text("Copied!");
            setTimeout(function () { $b.text("Copy"); }, 1500);
        });
    });

    $form.on("submit", function (e) {
        e.preventDefault();

        var payload = {
            brand_name: $("#brand_name").val().trim(),
            platform: $("#platform").val() || "",
            goal: $("#goal").val() || "",
            tone: $("#tone").val() || "",
            description: $("#description").val().trim()  // optional
        };

        // Lightweight client check; the server validates authoritatively.
        if (!payload.brand_name || !payload.platform || !payload.goal || !payload.tone) {
            showError("Please fill in all four fields.");
            return;
        }

        setLoading(true);

        $.ajax({
            url: "/api/generate/",
            method: "POST",
            contentType: "application/json",
            headers: { "X-CSRFToken": getCookie("csrftoken") },
            data: JSON.stringify(payload),
            success: function (response) {
                if (response && response.success) {
                    renderResult(response);
                } else {
                    show("#placeholder");
                    showError((response && response.error) || "Something went wrong.");
                }
            },
            error: function (xhr) {
                show("#placeholder");
                var msg = (xhr.responseJSON && xhr.responseJSON.error) || "Something went wrong. Please try again.";
                showError(msg);
            },
            complete: function () {
                setLoading(false);
            }
        });
    });
});
