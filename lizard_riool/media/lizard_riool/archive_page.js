$(function () {
    var set_active = function($checkbox, url) {
        $.post(url, "active=1", success=function () {
            $checkbox.closest("tr").attr("class", "success");
        });
    };

    var set_inactive = function($checkbox, url) {
        $.post(url, "active=0", success=function () {
            $checkbox.closest("tr").attr("class", "");
        });
    };

    var toggle_active = function () {
        var $t = $(this);
        var checked = $t.attr("checked");
        var url = $t.attr("data-activate-url");

        if (checked) {
            set_active($t, url);
        } else {
            set_inactive($t, url);
        }
    };

    var delete_sewerage = function() {
        var $t = $(this);
        var name = $t.attr("data-sewerage-name");
        var url = $t.attr("data-delete-url");

        if (confirm("Dit verwijdert het stelsel '"+name+"' uit de database, en ook de bijbehorende bestanden. Weet u het zeker?")) {

            $.ajax({
                url: url,
                type: 'DELETE',
                success: function () {
                    $t.closest("tr").remove();
                }});
        }
        return false; // Prevent default
    };

    $("input.toggle-active").click(toggle_active);
    $("button.remove-sewerage").click(delete_sewerage);
});
