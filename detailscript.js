let datecheck = document.getElementById("details");
datecheck.onsubmit = function() {
    if (!datecheck.room.value)
    {
        alert("Missing required: Room");
        return false;
    }
    else if (!datecheck.checkin.value)
    {
        alert("Missing required: Check-in Date");
        return false;
    }
    else if (!datecheck.checkout.value)
    {
        alert("Missing required: Check-out Date");
        return false;
    }
    return true;
};