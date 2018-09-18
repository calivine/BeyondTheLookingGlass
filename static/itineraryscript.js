var check_in = document.getElementById("in").innerHTML;
var check_out = document.getElementById("out").innerHTML;
var check_in_date = new Date(check_in);
var check_out_date = new Date(check_out);
var checkin = check_in_date.toDateString();
var checkout = check_out_date.toDateString();
document.getElementById("in").innerHTML = checkin;
document.getElementById("out").innerHTML = checkout;