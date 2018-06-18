let form = document.getElementById("booking2");
form.onsubmit = function() {
    if (form.guest.value == 0)
    {
        alert("Must enter at least 1 (one) guest");
        return false;
    }
    else if (!form.first.value)
    {
        alert("Missing required: First Name");
        return false;
    }
    else if (!form.last.value)
    {
        alert("Missing required: Last Name");
        return false;
    }
    else if (!form.username.value)
    {
        alert("Missing required: Username");
        return false;
    }
    else if (!form.password.value)
    {
        alert("Missing required: Password");
        return false;
    }
    else if (!form.email.value)
    {
        alert("Missing required: Email");
        return false;
    }
};