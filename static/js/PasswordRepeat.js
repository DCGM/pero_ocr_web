$(document).ready(function() {
  const invalidRepeatPassword = "Password and Repeat Password must be same.";

  var $registerPassword = $("#registerPassword");
  var $registerRepeatPassword = $("#registerRepeatPassword");

  function checkPasswords() {
    var registerPassword = $registerPassword.val();
    var registerRepeatPassword = $registerRepeatPassword.val();
    if (
      registerRepeatPassword !== "" &&
      registerPassword !== registerRepeatPassword
    ) {
      console.log("Valid");
      $registerRepeatPassword.addClass("is-invalid");
    } else {
      console.log("Invalid");
      $registerRepeatPassword.removeClass("is-invalid");
    }
  }

  $registerPassword.on("keyup", checkPasswords);
  $registerRepeatPassword.on("keyup", checkPasswords);
});
