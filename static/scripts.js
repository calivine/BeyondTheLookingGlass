let form = document.getElementById("registration");
form.onsubmit = function() {

    if (!form.email.value)
    {
        alert("Missing email");
        return false;
    }
    else if (!form.first.value)
    {
        alert("Must enter first name.");
        return false;
    }
    else if (!form.last.value)
    {
        alert("Must enter last name.");
        return false;
    }
    else if (!form.username.value)
    {
        alert("Must enter username");
        return false;
    }
    else if (!form.password.value)
    {
        alert("Must enter password");
        return false;
    }
    return true;

};