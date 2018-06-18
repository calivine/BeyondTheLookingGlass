let form = document.getElementById("hostreg");
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
    else if (!form.propname.value)
    {
        alert("Must enter a Property name");
        return false;
    }
    else if (!form.address.value)
    {
        alert("Must enter a street address");
        return false;
    }
    else if (!form.zipcode.value)
    {
        alert("Must enter a zipcode");
        return false;
    }
    else if (form.rooms.value === 0)
    {
        alert("Property must have at least one room");
    }
    return true;

};
