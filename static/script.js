$(document).ready(function() {
  var form = document.querySelector('form');
  form.onsubmit = function() {
    var about = document.querySelector('input[name=adminComment]');
    about.value = JSON.stringify(quill.getContents());
  
    console.log("Submitted", $(form).serialize(), $(form).serializeArray());
  
    alert('Open the console to see the submit data!')
    return false;
  };
});
