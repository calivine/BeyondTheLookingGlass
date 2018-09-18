let form = document.getElementById("login");
form.onsubmit = function() {
    if (!form.username.value)
    {
        alert("Missing required: Username");
        return false;
    }
    else if (!form.password.value)
    {
        alert("Missing required: Password");
        return false;
    }
    return true;

};

