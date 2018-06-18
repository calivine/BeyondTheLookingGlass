$(function() {
    $('#check').bind('click', function() {
        $.getJSON("/check_calendar/" + '{{ home }}', {
            room_name: $(':selected').val(),
            check_in: $('input[name = "checkin"]').val(),
            check_out: $('input[name = "checkout"]').val()
        }, function(data) {
            $("#result").text(data.result);
        });
        return false;
    });
});